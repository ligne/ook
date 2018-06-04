# vim: ts=4 : sw=4 : et

import datetime
import yaml
import sys

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
                print(date[:4], book.Scheduled, book.Title)
        print('----')


def _schedule(df, settings, date=datetime.date.today()):
    series = Series(
        author=settings.get('author'),
        series=settings.get('series'),
    )
    books = series.remaining()

    start = date.year
    if series.read_in_year(start):
        start += 1

    return _allocate(books, start, settings.get('rate', 1), settings.get('offset', 1))


# takes a df of unread books, and sets start dates
def _allocate(df, start, per_year=1, month=1):
    return [ ('{}-{:02d}-01'.format(ix+start, month), ii)
        for ix, (ii, row) in enumerate(df.iterrows()) ]


if __name__ == "__main__":
    import pandas as pd
    df = pd.read_csv('gr-api.csv', index_col=0).fillna('')
    df = df[~df['Exclusive Shelf'].isin(['to-read'])]
    df = df.drop_duplicates(['Work Id'])

    for column in ['Date Read', 'Date Added']:
        df[column] = pd.to_datetime(df[column])

    lint(df)
#     scheduled(df)

