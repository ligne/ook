# vim: ts=4 : sw=4 : et

import pandas as pd


GR_CSV    = 'data/goodreads.csv'
EBOOK_CSV = 'data/ebooks.csv'
EBOOK_CSV = 'data/wordcounts.csv'  # FIXME

words_per_page = 390

pd.options.display.max_rows = None
pd.options.display.max_colwidth = 40
pd.options.display.width = None


################################################################################

def _get_gr_books(csv=GR_CSV):
    # FIXME Published as a date would be nice too, except pandas doesn't
    # support very old dates.
    df = pd.read_csv(csv, index_col=0, parse_dates=[
        'Date Added',
        'Date Started',
        'Date Read',
        'Scheduled'
    ])

    df = df.rename(columns={
#        'Date Added': 'Added',
#        'Date Started': 'Started',
#        'Date Read': 'Read',
#        'Original Publication Year': 'Published',
#        'Number of Pages': 'Pages',
#        'Exclusive Shelf': 'Shelf',
#        'My Rating': 'Rating',
        'Average Rating': 'AvgRating',
        'Work Id': 'Work',
    })

    return df


def _save_gr_books(csv, df):
    pass


################################################################################

def _get_kindle_books(csv=EBOOK_CSV):
    df = pd.read_csv(csv, sep='\t', index_col=False)  # FIXME use proper csv

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

    df.Author.fillna('', inplace=True)

    df['Added'] = pd.to_datetime(df.mtime, unit='s')

    df = df.drop(['Words', 'file', 'mtime' ], axis='columns')

    # set an index that won't clash
    return df.set_index([['_'+str(ii) for ii in df.index]])


# FIXME maybe want this to not require pandas?
def _save_kindle_books(csv):
    pass


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
        shelves=None, categories=None, languages=None,
        gr_csv=GR_CSV, ebook_csv=EBOOK_CSV):

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
            df = df[df['Exclusive Shelf'].isin(shelves)]

        # load information about the authors

        self.df = df


    # save to disk.  FIXME must only apply to one file?
    def save():
        pass


if __name__ == "__main__":
    print(Collection().df)
    print(Collection().df.dtypes)

