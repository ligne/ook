# vim: ts=4 : sw=4 : et

import pytest

import itertools
import datetime
import pandas as pd

from reading.collection import Collection
from reading.scheduling import _dates, _allocate, _schedule
from reading.scheduling import scheduled_at


# load a test Collection
def _get_collection():
    return Collection(gr_csv='t/data/goodreads-2019-12-04.csv')


###############################################################################

def test__dates():

    it = _dates(2018)
    assert list(itertools.islice(it, 5)) == [
        '2018-01-01',
        '2019-01-01',
        '2020-01-01',
        '2021-01-01',
        '2022-01-01',
    ], 'One per year'

    it = _dates(2018, per_year=4)
    assert list(itertools.islice(it, 5)) == [
        '2018-01-01',
        '2018-04-01',
        '2018-07-01',
        '2018-10-01',
        '2019-01-01',
    ], 'Several per year'

    it = _dates(2018, per_year=3)
    assert list(itertools.islice(it, 5)) == [
        '2018-01-01',
        '2018-05-01',
        '2018-09-01',
        '2019-01-01',
        '2019-05-01',
    ], 'A different number per year'

    it = _dates(2018, offset=10)
    assert list(itertools.islice(it, 5)) == [
        '2018-10-01',
        '2019-10-01',
        '2020-10-01',
        '2021-10-01',
        '2022-10-01',
    ], 'Offset into the year'

    it = _dates(2018, per_year=2, offset=2)
    assert list(itertools.islice(it, 5)) == [
        '2018-02-01',
        '2018-08-01',
        '2019-02-01',
        '2019-08-01',
        '2020-02-01',
    ], 'Several a year, but offset'


def test_allocate():

    # only care about the index
    df = pd.DataFrame(index=range(10))

    it = _allocate(df, 2018)
    assert [d for (d, ix) in itertools.islice(it, 5)] == [
        '2018-01-01', '2019-01-01', '2020-01-01', '2021-01-01', '2022-01-01'
    ], 'Allocate with default options'

    it = _allocate(df, 2018, per_year=4)
    assert [d for (d, ix) in itertools.islice(it, 5)] == [
        '2018-01-01', '2018-04-01', '2018-07-01', '2018-10-01', '2019-01-01'
    ], 'Several a year'

    it = _allocate(df, 2018, offset=4)
    assert [d for (d, ix) in itertools.islice(it, 5)] == [
        '2018-04-01', '2019-04-01', '2020-04-01', '2021-04-01', '2022-04-01'
    ], 'Offset into the year'

    it = _allocate(df, 2018, skip=1)
    assert [d for (d, ix) in itertools.islice(it, 1)] == [
        '2019-01-01'
    ], 'Skip one (already read)'

    it = _allocate(df, 2018, skip=1, last_read=pd.Timestamp('2018-09-04'))
    assert [d for (d, ix) in itertools.islice(it, 1)] == [
        '2019-03-04'
    ], 'Postpone if read recently'


def _format_schedule(df, sched):
    return [(date, df.loc[ix].Title) for date, ix in sched]


def test__schedule():
    date = datetime.date(2019, 12, 4)

    df = _get_collection().df

    assert _format_schedule(df, _schedule(df, {
        'author': 'Le Guin',
    }, date=date)) == [
        ('2019-01-01', 'The Left Hand of Darkness'),
        ('2020-01-01', 'The Word For World Is Forest'),
        ('2021-01-01', 'The Earthsea Quartet'),
        ('2022-01-01', 'Orsinia'),
    ], 'By author, one per year'

    assert _format_schedule(df, _schedule(df, {
        'series': 'African Trilogy',
    }, date=date)) == [
        ('2019-01-01', 'Things Fall Apart'),
        ('2020-01-01', 'No Longer at Ease'),
        ('2021-01-01', 'Arrow of God'),
    ], 'By series, one per year'

    assert _format_schedule(df, _schedule(df, {
        'series': 'Culture',
        'start': 2029,
    }, date=date)) == [
        ('2029-01-01', 'Inversions'),
        ('2030-01-01', 'Look to Windward'),
        ('2031-01-01', 'Matter'),
        ('2032-01-01', 'Surface Detail'),
    ], 'Starting in a future year'

    assert _format_schedule(df, _schedule(df, {
        'author': 'Le Guin',
        'per_year': 2,
    }, date=date)) == [
        ('2019-01-01', 'The Left Hand of Darkness'),
        ('2019-07-01', 'The Word For World Is Forest'),
        ('2020-01-01', 'The Earthsea Quartet'),
        ('2020-07-01', 'Orsinia'),
    ], 'Several a year'

    assert _format_schedule(df, _schedule(df, {
        'series': 'Languedoc',
    }, date=date)) == [
        ('2020-01-01', 'Sepulchre'),
        ('2021-01-01', 'Citadel'),
    ], 'Already read this year'

    assert _format_schedule(df, _schedule(df, {
        'series': 'Languedoc',
        'force': 2019,
    }, date=date)) == [
        ('2019-08-07', 'Sepulchre'),  # still 6 months after the last one
        ('2020-01-01', 'Citadel'),
    ], 'Already read, but force'

    assert _format_schedule(df, _schedule(df, {
        'series': 'Languedoc',
        'force': 2018,
    }, date=date)) == [
        ('2020-01-01', 'Sepulchre'),
        ('2021-01-01', 'Citadel'),
    ], 'Force only works for the current year'

    assert _format_schedule(df, _schedule(df, {
        'series': 'Discworld',
        'per_year': 4,
    }, date=date)) == [
        ('2020-01-01', 'Maskerade'),
        ('2020-04-01', 'Hogfather'),
        ('2020-07-01', 'Jingo'),
        ('2020-10-01', 'The Truth'),
        ('2021-01-01', 'Night Watch'),
        ('2021-04-01', 'The Wee Free Men'),
        ('2021-07-01', 'Going Postal'),
        ('2021-10-01', 'Making Money'),
        ('2022-01-01', 'Unseen Academicals'),
        ('2022-04-01', 'I Shall Wear Midnight'),
        ('2022-07-01', 'Raising Steam'),
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

