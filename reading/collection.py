# vim: ts=4 : sw=4 : et

import re

import attr
import pandas as pd

from .config import config, merge_preferences
from .storage import load_df


pd.options.display.max_rows = None
pd.options.display.width = None


################################################################################

# split ebook titles into title, subtitle and volume parts, since they tend to
# be unusably messy
def _ebook_parse_title(title):
    title = re.sub(r'\s+', ' ', title.strip())

    t = title
    _s = v = None

    m = re.search(r'(?: / |\s?[;:] )', title)
    if m:
        t, _s = re.split(r'(?: / |\s?[;:] )', title, maxsplit=1)

    patterns = (
        (r', Tome ([IV]+)\.', 1),
        (r', Volume (\d+)(?: \(.+\))', 1),
        (r', tome (\w+)', 1),
    )

    for pat, grp in patterns:
        m = re.search(pat, title, re.IGNORECASE)
        if m:
            t = re.sub(pat, '', t)
            v = m.group(grp)
            break

    return pd.Series([t, v], index=['Title', 'Volume'])


# rearranges the fixes into something that DataFrame.update() can handle.
# FIXME clean up this mess
def _process_fixes(fixes):
    if not fixes:
        return None

    f = {}
    for fix in fixes.get('general', []):
        fix = {**fix}
        book_id = fix.pop('BookId')
        f[book_id] = fix

    for col, column_data in fixes.get('columns', {}).items():
        for val, ids in column_data.items():
            for book_id in ids:
                if book_id not in f:
                    f[book_id] = {}
                f[book_id][col] = val

    d = pd.DataFrame(f).T

    # FIXME looks like an upstream bug...
    # https://stackoverflow.com/questions/34667108/ignore-dates-and-times-while-parsing-yaml
    for column in ["Added", "Read", "Started"]:
        if column not in d.columns:
            continue
        d[column] = pd.to_datetime(d[column])

    return d


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
    def _validate_dedup_has_merge(self, _attribute, _value):
        if self.dedup and not self.merge:
            raise ValueError("dedup=True requires merge=True")

    def __attrs_post_init__(self):
        """Set up accounting for filtered books."""
        self.reset()

    ############################################################################

    @classmethod
    def from_dir(cls, csv_dir="data", fixes=True, metadata=True, **kwargs):
        """Create a collection from the contents of $csv_dir."""
        gr_df = load_df("goodreads", dirname=csv_dir)

        ebooks_df = load_df("ebooks", dirname=csv_dir).assign(
            # calculate page count
            Pages=lambda df: df.Words / config("kindle.words_per_page"),
            # set default columns
            Shelf="kindle",
            Binding="ebook",
            Borrowed=False,
            # FIXME not needed?
            Author=lambda df: df.Author.fillna(""),
        )

        df = pd.concat([gr_df, ebooks_df], sort=False)

        # Ensure the additional columns exist in any case
        df = df.assign(Gender=None, Nationality=None)
        if metadata:
            df.update(load_df("metadata", dirname=csv_dir))
            # load author information
            # FIXME this is very, very slow and should be moved into metadata.rebuild()
            authors = load_df("authors", dirname=csv_dir)
            df.update(
                df[df.AuthorId.isin(authors.index)]
                .AuthorId
                .apply(lambda x: authors.loc[x, ["Gender", "Nationality"]])
            )

        if fixes:
            df.update(load_df("scraped", dirname=csv_dir))
            fixes = _process_fixes(config("fixes"))
            if fixes is not None:
                df.update(fixes)

        return cls(df, **kwargs)

    def reset(self):
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
        ).assign(Entry=None)  # FIXME do something about Entry?

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

    def _filter_list(self, col, include, exclude):
        if include:
            self._df["_Mask"] &= self._df[col].isin(include)
        if exclude:
            self._df["_Mask"] &= ~self._df[col].isin(exclude)
        return self

    def shelves(self, include=None, exclude=None):
        """Filter the collection by shelf."""
        return self._filter_list("Shelf", include, exclude)

    def languages(self, include=None, exclude=None):
        """Filter the collection by language."""
        return self._filter_list("Language", include, exclude)

    def categories(self, include=None, exclude=None):
        """Filter the collection by category."""
        return self._filter_list("Category", include, exclude)

    def borrowed(self, state=None):
        """Filter the collection by borrowed status."""
        if state is not None:
            self._df["_Mask"] &= self._df.Borrowed == state
        return self


################################################################################

if __name__ == "__main__":
    print(Collection.from_dir().df.drop("AvgRating", axis="columns"))
    print(Collection.from_dir().df.dtypes)
