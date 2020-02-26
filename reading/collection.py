# vim: ts=4 : sw=4 : et

import re

import pandas as pd

from .config import config
from .storage import load_df, save_df


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
            df[df.Volume.notnull()].groupby(['Author', 'Title'], as_index=False).aggregate({
                **{col: 'first' for col in df.columns if col not in ('Author', 'Title', 'Entry', 'Volume')},
                **{'Pages': 'sum', "BookId": "first"},
            }),
        ], sort=False).set_index("BookId")

    return df


def _save_gr_books(_df):
    pass


################################################################################

def _get_kindle_books(csv=None, merge=False):
    df = load_df("ebooks", csv)

    # calculate page count
    df['Pages'] = df.Words / words_per_page

    if merge:
        df = df.drop('Title', axis=1).join(
            df.Title.apply(_ebook_parse_title)
        ).reset_index()

        df = pd.concat([
            df[df.Volume.isnull()],
            df[df.Volume.notnull()].groupby(['Author', 'Title'], as_index=False).aggregate({
                **{col: 'first' for col in df.columns if col not in ('Author', 'Title', 'Entry', 'Volume')},
                **{'Pages': 'sum', 'Words': 'sum', "BookId": "first"},
            }),
        ], sort=False).set_index("BookId")

    df = df.assign(Shelf="kindle", Binding="ebook", Borrowed=False)

    # FIXME not needed?
    df.Author.fillna('', inplace=True)

    return df


# FIXME maybe want this to not require pandas?
def _save_kindle_books(df, csv="data/ebooks.csv"):
    columns = [
        'Author',
        'Title',
        'Shelf',
        'Category',
        'Language',
        'Added',
        'Binding',
        'Words',
        'Borrowed'
    ]

    df = df[df.Shelf == 'kindle']

    save_df("ebooks", df[columns])


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
        book_id = fix.pop('BookId')
        f[book_id] = fix

    for col, data in fixes.get('columns', {}).items():
        for val, ids in data.items():
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

    def __init__(self, df=None,
                 gr_csv=None, ebook_csv=None,
                 dedup=False, merge=False,
                 fixes=True, metadata=True,
                 shelves=None, categories=None, languages=None, borrowed=None):
        # just wrap it
        if df is not None:
            self.df = df.copy()
            return

        # otherwise load and concatenate the CSV files
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

        if categories or shelves or languages or borrowed:
            import inspect
            caller = inspect.stack()[1]
            print(f"DEPRECATED ARGS: {caller.filename.split('/')[-1]}:{caller.function}:{caller.lineno}")

        # apply filters on shelf, language, category.
        if categories:
            df = df[df.Category.isin(categories)]
        if languages:
            df = df[df['Language'].isin(languages)]
        if shelves:
            df = df[df['Shelf'].isin(shelves)]
        if borrowed is not None:
            df = df[df['Borrowed'] == borrowed]

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
        return self._filter_list("Shelf", include, exclude)

    # filter by language
    def languages(self, include=None, exclude=None):
        return self._filter_list("Language", include, exclude)

    # filter by category
    def categories(self, include=None, exclude=None):
        return self._filter_list("Category", include, exclude)

    def borrowed(self, state=None):
        if state is not None:
            self.df = self.df[self.df.Borrowed == state]
        return self

    # save to disk.  FIXME must only apply to one file?
    def save(self):
        _save_gr_books(self.df)
        _save_kindle_books(self.df)


if __name__ == "__main__":
    print(Collection().df)
    print(Collection().df.dtypes)

