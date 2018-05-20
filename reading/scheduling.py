# vim: ts=4 : sw=4 : et

import datetime
import yaml
import sys


# options:
#   what to select
#       author
#       series
#   what order to use
#       publication date
#       series order
#       random -- >>> for ix in df.Title.apply(lambda x: x.__hash__()).sort_values().index: df.loc[ix].Title
#   missing books (for series only)
#       strict -- all books must be there; warn and leave gaps
#       ignore -- pretend gaps aren't there
#       break -- suspend when there's a gap.

# use cases:
#   reading through an author (Iain Banks)
#   with an offset into the year (Iain M. Banks)
#   reading a series (Rougon-Macquart)
#   with missing volumes
#   reading a series quickly (Discworld)


# used by:
#   suggestions.py in scheduled mode
#       year for $date only
#       might want to filter
#   lint.py for checking books are correctly allocated
#       no filtering, just check

def _get_schedules(f):
    with open(f) as fh:
        return yaml.load(fh)


# all the scheduled books
def scheduled(df, config='data/scheduled.yml'):
    # read the scheduling config
    schedules = _get_schedules(config)
    print(schedules)

    for settings in schedules:
        print(settings['author'])
        _schedule(df, settings)


def lint(df, config='data/scheduled.yml'):
    schedules = _get_schedules(config)

    horizon = str(datetime.date.today().year + 2)

    for settings in schedules:
        for date, book in _schedule(df, settings):
            book = df.loc[book]
            if float(date[:4]) != book.Scheduled and date[:4] <= horizon:
                print(date[:4], book.Scheduled, book.Title)
        print('----')


# FIXME dedup
def _schedule(df, settings, date=datetime.date.today()):
    # filter the books
    if 'author' in settings:
        df = df[df.Author == settings['author']]
    elif 'series' in settings:
        df = df[df.Series == settings['series']]

    # sort
    df = df.sort_values('Original Publication Year')

    # get unread books
    books = df[~df['Exclusive Shelf'].isin(['read', 'currently-reading'])]

    # allocate them to years
    per_year = settings.get('rate', 1)
    month = settings.get('month', 1)

    start = date.year
    if not _schedule_this_year(df, date.year):
        start += 1

    for ix, row in enumerate(books.iterrows()):
        print(ix+start, row[1].Title, int(row[1]['Original Publication Year']))
    print()

    return _allocate(books, start)


# takes a df of unread books, and sets start dates
def _allocate(df, start, per_year=1, month=1):
    return [ ('{}-{:02d}-01'.format(ix+start, month), ii)
        for ix, (ii, row) in enumerate(df.iterrows()) ]


# returns true if one of these needs to be scheduled for this year
# FIXME also currently reading
def _schedule_this_year(df, year):
    return not len(df[df['Date Read'].dt.year == year]) \
       and not len(df[df['Exclusive Shelf'] == 'currently-reading'])


if __name__ == "__main__":
    import pandas as pd
    df = pd.read_csv('gr-api.csv', index_col=0).fillna('')
    df = df[~df['Exclusive Shelf'].isin(['to-read'])]
    df = df.drop_duplicates(['Work Id'])

    for column in ['Date Read', 'Date Added']:
        df[column] = pd.to_datetime(df[column])

    lint(df)
#     scheduled(df)

