# vim: ts=4 : sw=4 : et

import sys
import datetime


# configuration:
#   series information cache.  build it from the series extracted from books.
#   series configuration.

# what to select
#   author
#   series
# what order to use
#   publication date
#   series order
#   random -- >>> df.loc[df.Title.apply(lambda x: x.__hash__()).sort_values().index].Title
#   date added
# missing books (for series only)
#   strict -- all books must be there; warn and leave gaps
#   ignore -- pretend gaps aren't there
#   break -- suspend when there's a gap.

# might be multiple volumes of the same work
#   subsume into volumes information
# might be the entirety of a series in one volume
#   get list of entries.
#   dedup
#   check if it matches the list from this volume.  and/or the count?
#   ignore if that's the case
# might not have an entry at all

# use-cases
#   scheduling
#   handling book data
#   linting for missing books?
#   hiding blocked books

# only trilogies need to be strict, so default to 'ignore'?

# FIXME this is horrible.
from .cache import load_yaml
cache = load_yaml('series')

import yaml
with open('data/config.yml') as fh:
    config = yaml.load(fh)


# books that should be hidden (because they're not the next in series or
# they're blocked by missing books.  should return a boolean pandas.Series so
# it can be used for slicing dataframes.
def hidden(df):
    pass


# converts an entries string into a list of integers
def _parse_entries(entries):
    if '-' in entries:
        start, end = entries.split('-')
        return list(range(int(start), int(end)+1))
    else:
        return [int(entries)]


# return the information for the series
# from cache and config?
def _get_series_settings(series):
    return {}


# whether to ignore the series.
def ignore(series_id):
    return int(series_id) in config['series']['ignore']


class Series():

    import pandas as pd
    _df = pd.read_csv('gr-api.csv', index_col=0, parse_dates=['Date Read', 'Date Added'], dtype={'Original Publication Year': str}, na_values=[]).drop_duplicates(['Work Id'])


    def __init__(self, author=None, series=None, settings=None, df=_df):
        # FIXME get settings for this series, and check
        if not settings:
            settings = _get_series_settings(series)

        # FIXME dedup
        df = df.drop_duplicates(['Work Id'])

        if author:
            # just work through in order
            self.author = author
            self.order = settings.get('order', 'published')
            self.missing = 'ignore'
            self.df = df[df.Author.str.contains(author)]
        elif series:
            self.series = series
            self.order = settings.get('order', 'series')
            self.missing = settings.get('missing', 'ignore')
            self.df = df[df.Series.fillna('').str.contains(series)]
        else:
            # error
            raise ValueError("Must provide either author or series.")
            pass


    # books in the series that still need to be read
    def remaining(self):
        sort_col = self.order == 'series' and 'Entry' or 'Original Publication Year'
        return self.df[~self.df['Exclusive Shelf'].isin(['read', 'currently-reading'])].sort_values(sort_col)


    # return readable ones in order (for scheduling)
    def readable(self):
        if self.missing == 'ignore':
            return self.remaining()
        # if 'strict', return leaving gaps
        # if 'break', return until the first blockage


    # returns true if the series has been read this year
    def read_in_year(self, year):
        return len(self.df[self.df['Date Read'].dt.year == year]) \
             + len(self.df[self.df['Exclusive Shelf'] == 'currently-reading'])


if __name__ == "__main__":
    (t, n) = sys.argv[1:3]
    if t == 'author':
        s = Series(author=n)
    elif t == 'series':
        s = Series(series=n)
    else:
        print("bad")
        sys.exit()

    print(s.remaining()[['Author', 'Series', 'Entry', 'Title']])

