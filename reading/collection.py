# vim: ts=4 : sw=4 : et

import pandas as pd
import re


GR_CSV    = 'data/goodreads.csv'
EBOOK_CSV = 'data/ebooks.csv'

words_per_page = 390

pd.options.display.max_rows = None
pd.options.display.max_columns = None
pd.options.display.max_colwidth = 40
pd.options.display.width = None


################################################################################

def _get_gr_books(csv=GR_CSV):
    # FIXME Published as a date would be nice too, except pandas doesn't
    # support very old dates.
    df = pd.read_csv(csv, index_col=0, parse_dates=[
        'Added',
        'Started',
        'Read',
        'Scheduled'
    ])

    return df


def _save_gr_books(csv, df):
    pass


################################################################################

def _get_kindle_books(csv=EBOOK_CSV):
    df = pd.read_csv(csv, index_col=0, parse_dates=[
        'Added',
    ])

    # fix author from metadata?
    # split title, subtitle, volume
    # fix up title (and subtitle?)

    # calculate page count
    df['Pages'] = df.Words / words_per_page

    # set missing columns
    df = df.assign(
        Binding='ebook',
        Borrowed=False,
        Shelf='kindle',
    )

    # FIXME not needed?
    df.Author.fillna('', inplace=True)

    return df


# FIXME maybe want this to not require pandas?
def _save_kindle_books(csv):
    pass


################################################################################

# split ebook titles into title, subtitle and volume parts, since they tend to
# be unusably messy
def _ebook_parse_title(title):
    title = re.sub('\s+', ' ', title.strip())

    t = title
    s = v = ''

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

    return t


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
                 dedup=False, merge=False, fixes='data/fixes.yml',
                 shelves=None, categories=None, languages=None, borrowed=None
                ):

        # just wrap it
        if df:
            self.df = df.copy()
            return self

        # otherwise load and concatenate the CSV files
        df = pd.concat([
            _get_gr_books(gr_csv),
            _get_kindle_books(ebook_csv),
        ])

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

        # load information about the authors

        self.df = df


    # save to disk.  FIXME must only apply to one file?
    def save():
        pass


if __name__ == "__main__":
    print(Collection().df)
    print(Collection().df.dtypes)

