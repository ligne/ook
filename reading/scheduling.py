# vim: ts=4 : sw=4 : et

import datetime
import pandas as pd

from .series import Series
from .config import config


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


# FIXME remove this
def scheduled(df):
    for settings in config('scheduled'):
        print(settings.get('author', settings.get('series')))
        for date, book in _schedule(df, **settings):
            book = df.loc[book]
            print('{} {} ({:0.0f})'.format(date, book.Title, book['Published']))
        print()


# mark all books that are scheduled to be read
def scheduled_books(df):
    s = pd.Series(False, df.index)

    for settings in config('scheduled'):
        s.loc[Series(
            author=settings.get('author'),
            series=settings.get('series'),
        ).df.index.intersection(df.index)] = True

    return s


# fix up df with the scheduled dates
def _set_schedules(df, schedules=None, date=datetime.date.today(), col='Scheduled'):
    for settings in schedules or config('scheduled'):
        for d, book in _schedule(df, **settings, date=date):
            df.loc[book, col] = d


# books ready to be read
#   FIXME delay if per_year == 1.  fix using most recent read date?
def scheduled_at(df, date=datetime.date.today(), schedules=None):
    _set_schedules(df, schedules, date)
    return df[(df.Scheduled.dt.year == date.year) & (df.Scheduled <= date)].sort_values('Title')


################################################################################

def _schedule(df, author=None, series=None,
              start=None, per_year=1, offset=0, force=False,
              date=datetime.date.today()):
    series = Series(
        author=author,
        series=series,
        df=df,
    )

    if not start:
        start = date.year

    dates = _dates(
        start, per_year, offset,
        force,
        last_read=series.last_read(),
        date=date,
    )

    return list(zip(dates, series.remaining().index))


# converts a stream of windows into a stream of dates for scheduling
def _dates(start, per_year=1, offset=1,
           force=False, last_read=None,
           date=datetime.date.today()):
    date = pd.Timestamp(date)
    windows = _windows(start, per_year, offset)

    for start, end in windows:
        # filter out windows that have passed
        if end < date:
            continue

        # check if it's been read
        if last_read:
            if last_read > start and not force:
                # skip to the next one.
                start, end = next(windows)

            # fix up the first one if necessary
            next_read = last_read + pd.DateOffset(months=6)
            if per_year == 1 and next_read > start:
                start = next_read

        yield start
        break

    # return the others
    for start, end in windows:
        yield start


# returns a stream of (start, end) dates which may or may not want a book
# allocating to them, starting at the beginning of year $start
def _windows(start, per_year=1, offset=1):
    start = pd.Timestamp(str(start))

    interval = 12 // per_year  # FIXME use divmod and check?
    interval = pd.DateOffset(months=interval)

    if offset > 1:
        start += pd.DateOffset(months=offset - 1)

    while True:
        end = start + interval
        yield (start, end)
        start = end


################################################################################

if __name__ == "__main__":
    from .collection import Collection
    df = Collection(shelves=['read', 'currently-reading', 'pending', 'elsewhere', 'ebooks', 'library']).df
    df = df.drop_duplicates(['Work'])

    date = datetime.date.today()

    scheduled(df)
    print('----')
    print('This year:')
    for ix, row in scheduled_at(df, datetime.date(date.year, 12, 31)).sort_values('Title').iterrows():
        print(' *', row.Title)
    print('----')
    print('Next year:')
    for ix, row in scheduled_at(df, datetime.date(date.year + 1, 12, 31)).sort_values('Title').iterrows():
        print(' *', row.Title)
    print('----')
    print('CURRENT:')
    for ix, row in scheduled_at(df, datetime.date.today()).sort_values('Title').iterrows():
        print(' *', row.Title)

