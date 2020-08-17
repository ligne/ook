# vim: ts=4 : sw=4 : et

import re

import attr
import pandas as pd

from .config import config, merge_preferences
from .storage import load_df


words_per_page = 390

pd.options.display.max_rows = None
pd.options.display.width = None


################################################################################

def _get_gr_books(csv=None, merge=False):
    df = load_df("goodreads", csv)

    if merge:
        df = df.drop("Title", axis=1).join(
            df.Title.str.extract("(?P<Title>.+?)(?: (?P<Volume>I+))?$", expand=True)
        ).reset_index()

        df = pd.concat([
            df[df.Volume.isnull()],
            df[df.Volume.notnull()].groupby(["Author", "Title"], as_index=False).aggregate(
                merge_preferences("goodreads")
            ),
        ], sort=False).set_index("BookId")

    return df


def _get_kindle_books(csv=None, merge=False):
    df = load_df("ebooks", csv)

    if merge:
        df = df.drop('Title', axis=1).join(
            df.Title.apply(_ebook_parse_title)
        ).reset_index()

        df = pd.concat([
            df[df.Volume.isnull()],
            df[df.Volume.notnull()].groupby(["Author", "Title"], as_index=False).aggregate(
                merge_preferences("ebooks")
            ),
        ], sort=False).set_index("BookId")

    # calculate page count
    df["Pages"] = df.Words / words_per_page

    df = df.assign(Shelf="kindle", Binding="ebook", Borrowed=False)

    # FIXME not needed?
    df.Author.fillna('', inplace=True)

    return df


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
    for column in ['Read', 'Started']:
        if column not in d.columns:
            continue
        d[column] = pd.to_datetime(d[column])

    return d


################################################################################

class Collection():

    # options:
    #   control dtype?
    #   control what fix-ups are enabled (for linting)
    #   control merging volumes
    #   control dedup (duplicate books;  duplicate ebooks;  ebooks that are
    #       also in goodreads)
    #   control visibility of later books in series

    def __init__(self, gr_csv=None, ebook_csv=None,
                 dedup=False, merge=False, fixes=True, metadata=True):
        # load and concatenate the CSV files
        df = pd.concat([
            _get_gr_books(gr_csv, merge),
            _get_kindle_books(ebook_csv, merge),
        ], sort=False)

        if metadata:
            df.update(load_df("metadata"))
            # load author information
            authors = load_df("authors")
            df = df.join(
                df[df.AuthorId.isin(authors.index)]
                .AuthorId
                .apply(lambda x: authors.loc[x, ["Gender", "Nationality"]])
            )

        if dedup:
            # FIXME to be implemented
            pass

        # take a clean copy before filtering
        self.all = df.copy()

        # apply fixes.
        if fixes:
            d = _process_fixes(config('fixes'))
            if d is not None:
                df.update(d)
            df.update(load_df("scraped"))

        self.df = df

    def _filter_list(self, col, include=None, exclude=None):
        if include:
            self.df = self.df[self.df[col].isin(include)]
        elif exclude:
            self.df = self.df[~self.df[col].isin(exclude)]

        return self

    # filter by shelf
    def shelves(self, include=None, exclude=None):
        """Filter the collection by shelf."""
        return self._filter_list("Shelf", include, exclude)

    # filter by language
    def languages(self, include=None, exclude=None):
        """Filter the collection by language."""
        return self._filter_list("Language", include, exclude)

    # filter by category
    def categories(self, include=None, exclude=None):
        """Filter the collection by category."""
        return self._filter_list("Category", include, exclude)

    def borrowed(self, state=None):
        """Filter the collection by borrowed status."""
        if state is not None:
            self.df = self.df[self.df.Borrowed == state]
        return self

    @property
    def read(self):
        """Return a dataframe of all read books."""
        return self.all[self.all.Shelf.isin(["read", "currently-reading"])]

    @property
    def read_authorids(self):
        """Return a list of the AuthorIds of all read authors."""
        return set(self.read.AuthorId)

    @property
    def recent_authorids(self):
        """Return a list of the AuthorIds of all recently read books."""

    @property
    def read_nationalities(self):
        """Return a list of all read nationalities."""
        return set(self.read.Nationality)


################################################################################

@attr.s
class NewCollection:
    """A collection of books."""

    _df = attr.ib(repr=lambda df: f"[{len(df)} books]")
    merge = attr.ib(default=False, kw_only=True)
    dedup = attr.ib(default=False, kw_only=True)

    # Add a column for tracking visibility
    def __attrs_post_init__(self):
        """Set up accounting for filtered books."""
        self.reset()

    @classmethod
    def from_dir(cls, csv_dir="data", _fixes=True, _metadata=True, **kwargs):
        """Create a collection from the contents of $csv_dir."""
        # load and concatenate the CSV files
        df = pd.concat([
            load_df("goodreads", f"{csv_dir}/goodreads.csv"),
            _get_kindle_books(csv=f"{csv_dir}/ebooks.csv", merge=False),
        ], sort=False)

        # FIXME apply fixes and metadata

        return cls(df, **kwargs)

    def reset(self):
        """Reset the state of the collection."""
        self._df["_Mask"] = True
        return self

    ### Access #################################################################

    @property
    def all(self):
        """Return a dataframe of all books in this collection."""
        # FIXME handle merge and dedup
        return self._df.drop("_Mask", axis="columns")

    # FIXME rename to something better?
    @property
    def df(self):
        """Return a dataframe of all selected books."""
        # FIXME handle merge and dedup
        return self._df[self._df["_Mask"]].drop("_Mask", axis="columns")

    @property
    def read(self):
        """Return a dataframe of books that have been read or are currently being read."""
        # FIXME this would include merge and dedup, but do we want this?
        return self.all[self.all.Shelf.isin(["read", "currently-reading"])]

    ### Filtering #############################################################

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
    print(Collection().df)
    print(Collection().df.dtypes)

