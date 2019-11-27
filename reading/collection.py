# vim: ts=4 : sw=4 : et

import pandas as pd
import re
import yaml


GR_CSV    = 'data/goodreads.csv'
EBOOK_CSV = 'data/ebooks.csv'

words_per_page = 390

pd.options.display.max_rows = None
pd.options.display.max_columns = None
pd.options.display.max_colwidth = 40
pd.options.display.width = None


################################################################################

def _get_gr_books(csv=GR_CSV, merge=False):
    # FIXME Published as a date would be nice too, except pandas doesn't
    # support very old dates.
    df = pd.read_csv(csv, parse_dates=[
        'Added',
        'Started',
        'Read',
        'Scheduled'
    ])

    if merge:
        s = df.Title.str.extract('(?P<Title>.+?)(?: (?P<Volume>I+))?$', expand=True)

        df = df.drop('Title', axis=1).join(s)
        df = pd.concat([
            df[df.Volume.isnull()],
            df[df.Volume.notnull()].groupby(['Author', 'Title'], as_index=False).aggregate({
                **{ col: 'first' for col in df.columns if col not in ('Author', 'Title', 'Entry', 'Volume') },
                **{'Pages': 'sum'},
            }),
        ])

    return df.set_index('BookId')


def _save_gr_books(df, csv=GR_CSV):
    pass


################################################################################

def _get_kindle_books(csv=EBOOK_CSV, merge=False):
    df = pd.read_csv(csv, parse_dates=[
        'Added',
    ])

    # calculate page count
    df['Pages'] = df.Words / words_per_page

    if merge:
        s = df.Title.apply(_ebook_parse_title)
        df = df.drop('Title', axis=1).join(s)
        df = pd.concat([
            df[df.Volume.isnull()],
            df[df.Volume.notnull()].groupby(['Author', 'Title'], as_index=False).aggregate({
                **{ col: 'first' for col in df.columns if col not in ('Author', 'Title', 'Entry', 'Volume') },
                **{'Pages': 'sum', 'Words': 'sum',},
            }),
        ])

    # FIXME not needed?
    df.Author.fillna('', inplace=True)

    return df.set_index('BookId')


# FIXME maybe want this to not require pandas?
def _save_kindle_books(df, csv=EBOOK_CSV):
    columns = ['Author','Title','Shelf','Category','Language','Added','Binding','Words','Borrowed']

    df = df[df.Shelf == 'kindle']

    df.sort_index()[columns].to_csv(csv, float_format='%g')


################################################################################

# split ebook titles into title, subtitle and volume parts, since they tend to
# be unusably messy
def _ebook_parse_title(title):
    title = re.sub('\s+', ' ', title.strip())

    t = title
    s = v = None

    m = re.search('(?: / |\s?[;:] )', title)
    if m:
        t, s = re.split('(?: / |\s?[;:] )', title, maxsplit=1)

    patterns = (
        (', Tome ([IV]+)\.', 1),
        (', Volume (\d+)(?: \(.+\))', 1),
        (', tome (\w+)', 1),
    )

    for pat, grp in patterns:
        m = re.search(pat, title, re.IGNORECASE)
        if m:
            t = re.sub(pat, '', t)
            v = m.group(grp)
            break

    return pd.Series([t, v], index=['Title', 'Volume'])


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
                 gr_csv=GR_CSV, ebook_csv=EBOOK_CSV,
                 dedup=False, merge=False,
                 fixes='data/fixes.yml', metadata='data/metadata.csv',
                 shelves=None, categories=None, languages=None, borrowed=None
                ):

        # just wrap it
        if df is not None:
            self.df = df.copy()
            return

        # otherwise load and concatenate the CSV files
        df = pd.concat([
            _get_gr_books(gr_csv, merge),
            _get_kindle_books(ebook_csv, merge),
        ])

        if metadata:
            df.update(pd.read_csv(metadata, index_col=0))
            # load author information FIXME ugh what a mess
            authors = pd.read_csv('data/authors.csv', index_col=0)
            a = df[df.AuthorId.isin(authors.index)].AuthorId
            df = pd.concat([
                df,
                a.apply(lambda x: authors.loc[x,['Gender', 'Nationality']]),
            ], axis='columns')

        # apply filters on shelf, language, category.
        if categories:
            df = df[df.Category.isin(categories)]
        else:
            # ignore articles unless explicitly requested
            df = df[~df.Category.isin(['articles'])]

        if languages:
            df = df[df['Language'].isin(languages)]
        if shelves:
            df = df[df['Shelf'].isin(shelves)]

        if borrowed is not None:
            df = df[df['Borrowed'] == borrowed]

        # FIXME load information about the authors

        # FIXME clean this up
        if fixes:
            with open('data/grfixes.yml') as fh:
                for col, data in yaml.load(fh).items():
                    for value, books in data.items():
                        a = []
                        for b in books:
                            a.append((b, value))
                        df.update(pd.DataFrame(a, columns=['BookId', col]).set_index(['BookId']))

        # apply fixes. FIXME
        if fixes:
            with open('data/fixes1.yml') as fh:
                d = pd.DataFrame(yaml.load(fh)).set_index(['BookId'])
                for column in ['Read', 'Started']:
                    d[column] = pd.to_datetime(d[column])
                df.update(d)

        self.df = df


    # save to disk.  FIXME must only apply to one file?
    def save(self):
        _save_gr_books(self.df)
        _save_kindle_books(self.df)


if __name__ == "__main__":
    print(Collection().df)
    print(Collection().df.dtypes)

