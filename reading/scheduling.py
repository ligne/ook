# vim: ts=4 : sw=4 : et

import datetime
import sys
import itertools
from dateutil.parser import parse

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


def scheduled(df):
    for settings in config('scheduled'):
        print(settings.get('author', settings.get('series')))
        for date, book in _schedule(df, settings):
            book = df.loc[book]
            print('{} {} ({:0.0f})'.format(date, book.Title, book['Published']))
        print()


# fix up df with the scheduled dates
def _set_schedules(df, scheduled=None, date=datetime.date.today(), col='Scheduled'):
    for settings in scheduled or config('scheduled'):
        for d, book in _schedule(df, settings, date):
            df.loc[book,col] = parse(d)


# books ready to be read
#   FIXME delay if per_year == 1.  fix using most recent read date?
def scheduled_at(df, date=datetime.date.today(), scheduled=None):
    _set_schedules(df, scheduled, date)
    return df[(df.Scheduled.dt.year == date.year)&(df.Scheduled <= date)].sort_values('Title')


# check the scheduled years are set correctly.
def lint(df):
    horizon = str(datetime.date.today().year + 3)

    _set_schedules(df, config('scheduled'), col='Sched')
    df = df[df.Sched.notnull()]  # ignore unscheduled or manually-scheduled books
    df = df[(df.Sched < horizon)&(df.Scheduled.dt.year != df.Sched.dt.year)]
    for ix, book in df.sort_values('Sched').iterrows():
        print('{} {} {} - https://www.goodreads.com/book/show/{}'.format(book.Sched.year, book.Scheduled.year, book.Title, ix))
    print('----')
    return df


def _schedule(df, settings, date=datetime.date.today()):
    series = Series(
        author=settings.get('author'),
        series=settings.get('series'),
        df=df,
    )
    start = settings.get('start', date.year)
    per_year = settings.get('per_year', 1)

    if settings.get('force') == date.year:
        skip = 0
    else:
        # "slots" count even if no book was read in that time
        passed = int(date.timetuple().tm_yday / 365 * per_year)
        skip = min(max(series.read_in_year(start), passed), per_year)

    return _allocate(
        series.remaining(),
        start=start,
        per_year=per_year,
        offset=settings.get('offset', 1),
        skip=skip,
    )


# takes a df of unread books, and sets start dates
def _allocate(df, start, per_year=1, offset=1, skip=0):
    dates = itertools.islice(_dates(start, per_year, offset), skip, None)
    return [ (date, ix) for date, ix in zip(dates, df.index) ]


def _dates(start, per_year=1, offset=1):
    # work out which months to use
    months = [x+offset for x in range(12) if not x % (12/per_year)]

    for year in itertools.count(start):
        for month in months:
            yield '{}-{:02d}-01'.format(year, month)


if __name__ == "__main__":
    from .collection import Collection
    df = Collection(shelves=['read', 'currently-reading', 'pending', 'elsewhere', 'ebooks', 'library']).df
    df = df.drop_duplicates(['Work'])

    lint(df)
    print('----')
    scheduled(df)
    print('----')
    for ix, row in scheduled_at(df, datetime.date(2019, 12, 31)).sort_values('Title').iterrows():
        print(row.Title)
    print('----')
    for ix, row in scheduled_at(df, datetime.date(2018, 10, 2)).sort_values('Title').iterrows():
        print(row.Title)
    print('----')
    print('CURRENT:\n')
    for ix, row in scheduled_at(df, datetime.date.today()).sort_values('Title').iterrows():
        print(row.Title)

