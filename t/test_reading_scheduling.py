# vim: ts=4 : sw=4 : et

import itertools
import datetime
import pandas as pd

from reading.collection import Collection
from reading.scheduling import _windows, _dates, _schedule
from reading.scheduling import scheduled_at


# load a test Collection
def _get_collection():
    return Collection(gr_csv='t/data/goodreads-2019-12-04.csv', fixes=False)


###############################################################################

def _format_windows(it, count=5):
    formatted = []
    for row in itertools.islice(it, count):
        formatted.append(tuple(str(x.date()) for x in row))
    return formatted


def test__windows():
    it = _windows(2018)
    assert _format_windows(it, 5) == [
        ('2018-01-01', '2019-01-01'),
        ('2019-01-01', '2020-01-01'),
        ('2020-01-01', '2021-01-01'),
        ('2021-01-01', '2022-01-01'),
        ('2022-01-01', '2023-01-01'),
    ], 'One per year'

    it = _windows(2018, per_year=4)
    assert _format_windows(it) == [
        ('2018-01-01', '2018-04-01'),
        ('2018-04-01', '2018-07-01'),
        ('2018-07-01', '2018-10-01'),
        ('2018-10-01', '2019-01-01'),
        ('2019-01-01', '2019-04-01'),
    ], 'Several per year'

    it = _windows(2018, per_year=3)
    assert _format_windows(it) == [
        ('2018-01-01', '2018-05-01'),
        ('2018-05-01', '2018-09-01'),
        ('2018-09-01', '2019-01-01'),
        ('2019-01-01', '2019-05-01'),
        ('2019-05-01', '2019-09-01'),
    ], 'A different number per year'

    it = _windows(2018, offset=10)
    assert _format_windows(it) == [
        ('2018-10-01', '2019-10-01'),
        ('2019-10-01', '2020-10-01'),
        ('2020-10-01', '2021-10-01'),
        ('2021-10-01', '2022-10-01'),
        ('2022-10-01', '2023-10-01'),
    ], 'Offset into the year'

    it = _windows(2018, per_year=2, offset=2)
    assert _format_windows(it) == [
        ('2018-02-01', '2018-08-01'),
        ('2018-08-01', '2019-02-01'),
        ('2019-02-01', '2019-08-01'),
        ('2019-08-01', '2020-02-01'),
        ('2020-02-01', '2020-08-01'),
    ], 'Several a year, but offset'


################################################################################

def _format_dates(it, count=5):
    return [str(x.date()) for x in itertools.islice(it, count)]


# starting early in the year
def test__dates_early_year():
    date = datetime.date(2020, 2, 4)

    it = _dates(
        start=date.year,
        date=date,
    )
    assert _format_dates(it) == [
        '2020-01-01',
        '2021-01-01',
        '2022-01-01',
        '2023-01-01',
        '2024-01-01',
    ], 'One per year, start of year'

    it = _dates(
        start=date.year,
        per_year=4,
        date=date,
    )
    assert _format_dates(it) == [
        '2020-01-01',
        '2020-04-01',
        '2020-07-01',
        '2020-10-01',
        '2021-01-01',
    ], 'Several per year, start of year'

    it = _dates(
        start=date.year,
        last_read=pd.Timestamp('2020-01-04'),
        date=date,
    )
    assert _format_dates(it) == [
        '2021-01-01',
        '2022-01-01',
        '2023-01-01',
        '2024-01-01',
        '2025-01-01',
    ], 'Read this year'

    it = _dates(
        start=date.year,
        last_read=pd.Timestamp('2020-01-04'),
        force=True,
        date=date,
    )
    assert _format_dates(it) == [
        '2020-07-04',  # first is delayed
        '2021-01-01',
        '2022-01-01',
        '2023-01-01',
        '2024-01-01',
    ], 'Read this year, but force'

    it = _dates(
        start=date.year,
        last_read=pd.Timestamp('2019-12-04'),
        date=date,
    )
    assert _format_dates(it) == [
        '2020-06-04',  # first is delayed
        '2021-01-01',
        '2022-01-01',
        '2023-01-01',
        '2024-01-01',
    ], 'Read late last year'

    it = _dates(
        start=date.year,
        per_year=4,
        last_read=pd.Timestamp('2019-12-04'),
        date=date,
    )
    assert _format_dates(it) == [
        '2020-01-01',
        '2020-04-01',
        '2020-07-01',
        '2020-10-01',
        '2021-01-01',
    ], 'Dates are only adjusted when per_year=1'


# starting part-way through the year
def test__dates_mid_year():
    date = datetime.date(2020, 5, 4)

    it = _dates(
        start=date.year,
        per_year=4,
        date=date,
    )
    assert _format_dates(it, 1) == [
        '2020-04-01',
    ], 'Skipped a window'


# starting late in the year
def test__dates_late_year():
    date = datetime.date(2019, 12, 4)

    it = _dates(
        start=date.year,
        date=date,
    )
    assert _format_dates(it) == [
        '2019-01-01',
        '2020-01-01',
        '2021-01-01',
        '2022-01-01',
        '2023-01-01',
    ], 'One per year, end of year'

    it = _dates(
        start=date.year,
        per_year=4,
        date=date,
    )
    assert _format_dates(it) == [
        '2019-10-01',
        '2020-01-01',
        '2020-04-01',
        '2020-07-01',
        '2020-10-01',
    ], 'Several per year, end of year'

    it = _dates(
        start=date.year,
        last_read=pd.Timestamp('2019-04-04'),
        date=date,
    )
    assert _format_dates(it) == [
        '2020-01-01',
        '2021-01-01',
        '2022-01-01',
        '2023-01-01',
        '2024-01-01',
    ], 'Read this year'

    it = _dates(
        start=date.year,
        last_read=pd.Timestamp('2019-08-26'),
        date=date,
    )
    assert _format_dates(it) == [
        '2020-02-26',
        '2021-01-01',
        '2022-01-01',
        '2023-01-01',
        '2024-01-01',
    ], 'Read late this year: next year is postponed'

    it = _dates(
        start=date.year,
        per_year=4,
        date=date,
    )
    assert _format_dates(it, 1) == [
        '2019-10-01',
    ], 'Skipped several windows'


# starting in the future
def test__dates_future():
    date = datetime.date(2019, 12, 4)

    it = _dates(start=2021, date=date)
    assert _format_dates(it) == [
        '2021-01-01',
        '2022-01-01',
        '2023-01-01',
        '2024-01-01',
        '2025-01-01',
    ], 'Starting in a future year'


################################################################################

def _format_schedule(df, sched):
    return [(str(date.date()), df.loc[ix].Title) for date, ix in sched]


def test__schedule():
    date = datetime.date(2019, 12, 4)

    df = _get_collection().df

    assert _format_schedule(df, _schedule(df, **{
        'author': 'Le Guin',
    }, date=date)) == [
        ('2019-01-01', 'The Left Hand of Darkness'),
        ('2020-01-01', 'The Word For World Is Forest'),
        ('2021-01-01', 'The Earthsea Quartet'),
        ('2022-01-01', 'Orsinia'),
    ], 'By author, one per year'

    assert _format_schedule(df, _schedule(df, **{
        'series': 'African Trilogy',
    }, date=date)) == [
        ('2019-01-01', 'Things Fall Apart'),
        ('2020-01-01', 'No Longer at Ease'),
        ('2021-01-01', 'Arrow of God'),
    ], 'By series, one per year'

    assert _format_schedule(df, _schedule(df, **{
        'series': 'Culture',
        'start': 2029,
    }, date=date)) == [
        ('2029-01-01', 'Inversions'),
        ('2030-01-01', 'Look to Windward'),
        ('2031-01-01', 'Matter'),
        ('2032-01-01', 'Surface Detail'),
    ], 'Starting in a future year'

    assert _format_schedule(df, _schedule(df, **{
        'author': 'Le Guin',
        'per_year': 2,
    }, date=date)) == [
        ('2019-07-01', 'The Left Hand of Darkness'),
        ('2020-01-01', 'The Word For World Is Forest'),
        ('2020-07-01', 'The Earthsea Quartet'),
        ('2021-01-01', 'Orsinia'),
    ], 'Several a year, late in year: skips first window'

    assert _format_schedule(df, _schedule(df, **{
        'series': 'Languedoc',
    }, date=date)) == [
        ('2020-01-01', 'Sepulchre'),
        ('2021-01-01', 'Citadel'),
    ], 'Already read this year'

    assert _format_schedule(df, _schedule(df, **{
        'series': 'Languedoc',
        'force': 2019,
    }, date=date)) == [
        ('2019-08-07', 'Sepulchre'),  # still 6 months after the last one
        ('2020-01-01', 'Citadel'),
    ], 'Already read, but force'

#    assert _format_schedule(df, _schedule(df, **{
#        'series': 'Languedoc',
#    }, date=date)) == _format_schedule(df, _schedule(df, **{
#        'series': 'Languedoc',
#        'force': 2018,
#    }, date=date)), 'Force only works for the current year'

    assert _format_schedule(df, _schedule(df, **{
        'series': 'Discworld',
        'per_year': 4,
    }, date=date))[:3] == [
        ('2020-01-01', 'Maskerade'),
        ('2020-04-01', 'Hogfather'),
        ('2020-07-01', 'Jingo'),
    ], 'Several per year but missed a slot'

    # FIXME other Series options get passed through?


# format a dataframe schedule
def _format_scheduled_df(sched):
    return [row.Title for ix, row in sched.iterrows()]


def test_scheduled_at():
    c = _get_collection()
    df = c.df

    s = [
        {'author': 'Haruki Murakami'},  # just an author
        {'author': 'Iain Banks', 'offset': 4},  # offset
        {'series': 'Discworld$', 'per_year': 4},  # multiple
        {'series': 'Leatherstocking Tales', 'start': 2020},  # start later
        {'series': 'Languedoc', 'force': 2019},  # force
    ]

    assert _format_scheduled_df(scheduled_at(df, date=datetime.date(2019, 12, 4), schedules=s)) == [
        'La Conquête de Plassans',
        'Sepulchre'
    ], 'One unread book, one forced'

#    assert _format_scheduled_df(scheduled_at(df, date=datetime.date(2020, 1, 1), schedules=s)) == [
#    ]

