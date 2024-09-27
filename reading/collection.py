# vim: ts=4 : sw=4 : et

"""Represents a collection of books."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
import re
from typing import List, Optional, Sequence

import attr
import pandas as pd
from typing_extensions import Self

from .chain import Chain
from .config import Config, df_columns, merge_preferences, metadata_prefer
from .storage import Store, load_df


pd.set_option("display.max_rows", None)
pd.set_option("display.width", None)


################################################################################


def _ebook_metadata_overlay(ebooks: pd.DataFrame, works: pd.DataFrame) -> pd.DataFrame:
    return ebooks[[]].join(works.drop(columns=["BookId", "Category"]), how="left")


def _author_overlay(
    base: pd.DataFrame, authors: pd.DataFrame, author_fixes: pd.DataFrame
) -> pd.DataFrame:
    authors = authors.reindex(authors.index.union(author_fixes.index))
    authors.update(author_fixes)
    return (
        base[["AuthorId"]]
        .join(authors[["Gender", "Nationality"]], on="AuthorId", how="inner")
        .drop(columns="AuthorId")
        .sort_index()
    )


def rebuild_metadata(store: Store, config: Config) -> Store:
    """Refresh the metadata tables in $store."""
    author_fixes = pd.DataFrame(config("authors"))
    if not author_fixes.empty:
        author_fixes = author_fixes.set_index("AuthorId")
    authors = store.authors
    # fixed_authors = authors.reindex(authors.index | author_fixes.index)

    # goodreads and ebooks have to be done separately, because pandas does not
    # like indexes containing multiple types

    # ebooks
    base = store.ebooks.reindex(columns=df_columns("metadata"))
    metadata = base.copy()
    metadata.update(_ebook_metadata_overlay(metadata, store.books))
    metadata.update(_author_overlay(metadata, authors, author_fixes))
    store.ebook_metadata = metadata.where(base != metadata).dropna(how="all", axis="index")

    # goodreads
    base = store.goodreads.reindex(columns=df_columns("metadata"))
    metadata = base.copy()
    metadata.update(_author_overlay(metadata, authors, author_fixes))
    store.gr_metadata = metadata.where(base != metadata).dropna(how="all", axis="index")

    return store


################################################################################


# split ebook titles into title, subtitle and volume parts, since they tend to
# be unusably messy
def _ebook_parse_title(title):
    title = re.sub(r"\s+", " ", title.strip())

    t = title
    _s = v = None

    m = re.search(r"(?: / |\s?[;:] )", title)
    if m:
        t, _s = re.split(r"(?: / |\s?[;:] )", title, maxsplit=1)

    patterns = (
        (r", Tome ([IV]+)\.", 1),
        (r", Volume (\d+)(?: \(.+\))", 1),
        (r", tome (\w+)", 1),
    )

    for pat, grp in patterns:
        m = re.search(pat, title, re.IGNORECASE)
        if m:
            t = re.sub(pat, "", t)
            v = m.group(grp)
            break

    return pd.Series([t, v], index=["Title", "Volume"])


# rearranges the fixes into something that DataFrame.update() can handle.
# FIXME clean up this mess. and move into the config module?
def _process_fixes(fixes):
    if not fixes:
        return pd.DataFrame()

    fix_df = pd.DataFrame(fixes).set_index("BookId")

    # remove any duplicates
    # FIXME merge them
    fix_df = fix_df[~fix_df.index.duplicated(keep="last")]

    # FIXME looks like an upstream bug...
    # https://stackoverflow.com/questions/34667108/ignore-dates-and-times-while-parsing-yaml
    for column in ["Added", "Read", "Started"]:
        if column in fix_df.columns:
            fix_df[column] = pd.to_datetime(fix_df[column])

    return fix_df


# FIXME make words_per_page optional and/or set in the constructor? it's not
# always relevant(?) and it would allow this to be done automatically in the
# Store...
def expand_ebooks(ebooks, words_per_page):
    """Set default/derived columns on the ebooks dataframe."""
    return ebooks.assign(
        Shelf="kindle",
        Borrowed=False,
        Binding="ebook",
        Pages=round(ebooks.Words / words_per_page),
        # FIXME not needed?
        Author=ebooks.Author.fillna(""),
    )


################################################################################


def read_authorids(c):
    """Return a list of the AuthorIds of all read authors."""
    return set(c.read.AuthorId)


def recent_authorids(_c):
    """Return a list of the AuthorIds of all recently read books."""


def read_nationalities(c):
    """Return a list of all read nationalities."""
    return set(c.read.Nationality)


################################################################################


def _merge_id(book):
    """Generate a merge key for $book."""
    # groups share the same author and title, but have distinct, non-null volumes.
    # FIXME want to work **without** metadata or the ebook titles will be broken.
    # FIXME generate these as part of metadata.rebuild()? would also solve the
    # problem above if we extract the volume/title at the same time...
    if book.Shelf == "kindle":
        cleaned = _ebook_parse_title(book.Title)
        title = cleaned.Title
        volume = cleaned.Volume
    else:
        title, volume = re.match("(?P<Title>.+?)(?: (?P<Volume>I+))?$", book.Title).groups()

    # [author, canonical title], but only if there's a volume number.
    return f"{book.Author}|{title}" if volume else book.name


def _merged_title(book):
    """Return the canonical title for $book."""
    if book.Shelf == "kindle":
        return _ebook_parse_title(book.Title).Title if book.Category != "articles" else book.Title
    else:
        return re.match("(?P<Title>.+?)(?: (?P<Volume>I+))?$", book.Title).group("Title")


@attr.s
class Collection:
    """A collection of books."""

    _df = attr.ib(repr=lambda df: f"[{len(df)} books]")
    merge = attr.ib(default=False, kw_only=True)
    dedup = attr.ib(default=False, kw_only=True)

    @dedup.validator
    def _validate_dedup_has_merge(self, _attribute, _value) -> None:
        if self.dedup and not self.merge:
            raise ValueError("dedup=True requires merge=True")

    def __attrs_post_init__(self) -> None:
        """Set up calculated columns and accounting for filtered books."""
        df = self._df
        # cast to timedelta or it explodes when there are no read books
        duration = (df.Read - df.Started).astype("timedelta64[ns]").dt.days + 1
        self._df = df.assign(
            Duration=duration,
            Rate=round(df.Pages / duration),
        )
        self.reset()

    ############################################################################

    @classmethod
    def from_dir(
        cls,
        csv_dir: str = "data",
        fixes: bool = True,
        metadata: bool = True,
        **kwargs,
    ) -> Self:
        """Create a collection from the contents of $csv_dir."""
        return cls.from_store(
            store=Store(csv_dir),
            config=Config.from_file(Path(csv_dir, "config.yml")),
            fixes=fixes,
            metadata=metadata,
            **kwargs,
        )

    @classmethod
    def from_store(
        cls,
        store: Store,
        config: Config,
        fixes: bool = True,
        metadata: bool = True,
        **kwargs,
    ) -> Self:
        """Create a Collection from a Store object."""
        gr_df = store.goodreads
        ebooks_df = expand_ebooks(store.ebooks, words_per_page=config("kindle.words_per_page"))

        df = pd.concat([gr_df, ebooks_df], sort=False)

        # Ensure the additional columns exist in any case
        # FIXME use reindex to expand it to give it the right columnns
        df = df.assign(Gender=None, Nationality=None)

        if metadata:
            df.update(store.ebook_metadata)
            df.update(store.gr_metadata)

        if fixes:
            df.update(store.scraped)
            df.update(_process_fixes(config("fixes")))

        return cls(df, **kwargs)

    def reset(self) -> Self:
        """Reset the state of the collection."""
        self._df["_Mask"] = True
        return self

    ### Merging/dedup ##########################################################

    def _merged(self):
        """Return all the books, merged."""
        df = self._df.assign(
            MergeId=self._df.apply(_merge_id, axis="columns"),
            Title=self._df.apply(_merged_title, axis="columns"),
        )

        return (
            df.reset_index()
            .groupby("MergeId", as_index=False, sort=False)
            .aggregate(merge_preferences())
            .set_index("BookId")
            .assign(Entry=None)  # FIXME do something about Entry?
        )

    ### Scheduling #############################################################

    def set_schedules(self, schedules) -> Self:
        """Set the schedules according to the rules in $schedules."""
        pairs = []

        for schedule in schedules:
            # work out what we're scheduling
            try:
                # use _df directly here to avoid merging, which is (currently) very slow
                if "author" in schedule:
                    chain = Chain.from_author_name(self._df, schedule["author"])
                elif "series" in schedule:
                    chain = Chain.from_series_name(self._df, schedule["series"])
                else:
                    raise ValueError("Schedule must specify at least one of 'author' or 'series'")
            except IndexError:
                continue

            # schedule using the other arguments
            pairs.extend(
                chain.schedule(
                    **{k: v for k, v in schedule.items() if k not in {"author", "series"}}
                )
            )

        if pairs:
            index, scheduled = zip(*pairs)
            sched = pd.Series(data=scheduled, index=index, name="Scheduled")
            if sched.index.duplicated().any():
                # FIXME warn
                sched = sched[~sched.index.duplicated(keep="last")]
            self._df.update(sched)

        return self

    ### Access #################################################################

    @property
    def all(self):
        """Return a dataframe of all books in this collection."""
        # FIXME handle dedup
        df = self._merged() if self.merge else self._df
        return df.drop("_Mask", axis="columns")

    # FIXME rename to something better?
    @property
    def df(self):
        """Return a dataframe of all selected books."""
        # FIXME handle dedup
        df = self._merged() if self.merge else self._df
        return df[df["_Mask"]].drop("_Mask", axis="columns")

    @property
    def read(self):
        """Return a dataframe of books that have been read or are currently being read."""
        # FIXME this would include merge and dedup, but do we want this?
        return self.all[self.all.Shelf.isin(["read", "currently-reading"])]

    ### Filtering ##############################################################

    def _filter_list(self, col: str, selection: Sequence[str], exclude: bool) -> Self:
        if selection:
            self._df["_Mask"] &= self._df[col].isin(selection) ^ exclude
        return self

    def shelves(self, *selection: str, exclude: bool = False) -> Self:
        """Filter the collection by shelf."""
        return self._filter_list("Shelf", selection, exclude)

    def languages(self, *selection: str, exclude: bool = False) -> Self:
        """Filter the collection by language."""
        return self._filter_list("Language", selection, exclude)

    def categories(self, *selection: str, exclude: bool = False) -> Self:
        """Filter the collection by category."""
        return self._filter_list("Category", selection, exclude)

    def borrowed(self, state: Optional[bool] = None) -> Self:
        """Filter the collection by borrowed status."""
        # FIXME None so the caller doesn't have to care if it was actually set
        if state is not None:
            self._df["_Mask"] &= self._df.Borrowed == state
        return self

    def scheduled(self, *, exclude: bool = False) -> Self:
        """Filter the collection by scheduled status."""
        self._df["_Mask"] &= self._df.Scheduled.notna() ^ exclude
        return self

    def scheduled_at(self, date: dt.date) -> Self:
        """Select only books scheduled to be read at $date."""
        self._df["_Mask"] &= (self._df.Scheduled.dt.year == date.year) & (
            self._df.Scheduled <= date
        )
        return self


################################################################################

if __name__ == "__main__":
    print(Collection.from_dir().df.drop("AvgRating", axis="columns"))
    print(Collection.from_dir().df.dtypes)
