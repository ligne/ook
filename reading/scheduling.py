# vim: ts=4 : sw=4 : et

import datetime
import sys
import itertools

from .series import Series


import yaml
with open('data/config.yml') as fh:
    config = yaml.load(fh)

# use cases:
#   reading through an author (Haruki Murakami)
#   with an offset into the year (Iain M. Banks)
#   reading a series (Rougon-Macquart)
#   series with missing volumes -- both strict and break
#   reading several books a year (Discworld)

# used by:
#   suggestions.py in scheduled mode
#       year for $date only
#       might want to filter
#   lint.py
#       no filtering, just check
#   reading.py
#       identifying books for each scheduled year


def scheduled(df):
    for settings in config['scheduled']:
        print(settings.get('author', settings.get('series')))
        for date, book in _schedule(df, settings):
            book = df.loc[book]
            print(date, book.Title, int(book['Original Publication Year']))
        print()


def lint(df):
    horizon = str(datetime.date.today().year + 2)

    for settings in config['scheduled']:
        for date, book in _schedule(df, settings):
            book = df.loc[book]
            if float(date[:4]) != book.Scheduled and date[:4] <= horizon:
                print(date[:4], book.Scheduled, book.Title, 'https://www.goodreads.com/book/show/{}'.format(book.name))
        print('----')


def _schedule(df, settings, date=datetime.date.today()):
    series = Series(
        author=settings.get('author'),
        series=settings.get('series'),
        df=df,
    )

    return _allocate(
        series.remaining(),
        start=date.year,
        per_year=settings.get('per_year', 1),
        offset=settings.get('offset', 1),
        skip=series.read_in_year(date.year)
    )


# takes a df of unread books, and sets start dates
def _allocate(df, start, per_year=1, offset=1, skip=0):
    return [ (date, ix) for date, (ix, row) in zip(_dates(start, per_year, offset, min(per_year, skip)), df.iterrows()) ]


def _dates(start, per_year=1, offset=1, skip=0):
    # work out which months to use
    months = [x+offset for x in range(12) if not x % (12/per_year)]

    for year in itertools.count(start):
        for month in months:
            if skip:
                skip -= 1
                continue

            yield '{}-{:02d}-01'.format(year, month)


if __name__ == "__main__":
    import pandas as pd
    df = pd.read_csv('gr-api.csv', index_col=0, parse_dates=['Date Read', 'Date Added'], dtype={'Original Publication Year': float}, na_values=[])
    df = df[~df['Exclusive Shelf'].isin(['to-read'])]
    df = df.drop_duplicates(['Work Id'])

    lint(df)
    scheduled(df)

