# vim: ts=4 : sw=4 : et

import nose
from nose.tools import *

import pandas as pd
import itertools
import datetime

from io import StringIO

import reading.scheduling


def test__dates():

    # one a year
    it = reading.scheduling._dates(2018)
    eq_(list(itertools.islice(it, 5)), [
        '2018-01-01',
        '2019-01-01',
        '2020-01-01',
        '2021-01-01',
        '2022-01-01',
    ])

    # several a year
    it = reading.scheduling._dates(2018, per_year=4)
    eq_(list(itertools.islice(it, 5)), [
        '2018-01-01',
        '2018-04-01',
        '2018-07-01',
        '2018-10-01',
        '2019-01-01',
    ])

    # several a year
    it = reading.scheduling._dates(2018, per_year=3)
    eq_(list(itertools.islice(it, 5)), [
        '2018-01-01',
        '2018-05-01',
        '2018-09-01',
        '2019-01-01',
        '2019-05-01',
    ])

    # offset into the year
    it = reading.scheduling._dates(2018, offset=10)
    eq_(list(itertools.islice(it, 5)), [
        '2018-10-01',
        '2019-10-01',
        '2020-10-01',
        '2021-10-01',
        '2022-10-01',
    ])

    # multiple, offset
    it = reading.scheduling._dates(2018, per_year=2, offset=2)
    eq_(list(itertools.islice(it, 5)), [
        '2018-02-01',
        '2018-08-01',
        '2019-02-01',
        '2019-08-01',
        '2020-02-01',
    ])

    # only one remaining this year
    it = reading.scheduling._dates(2018, per_year=4, skip=3)
    eq_(list(itertools.islice(it, 5)), [
        '2018-10-01',
        '2019-01-01',
        '2019-04-01',
        '2019-07-01',
        '2019-10-01',
    ])


def test_schedule():

    # one a year, already read this year
    # multiple a year, already read this year

    ############################################################################

    df = pd.read_csv(StringIO("""
Book Id,Author,Author Id,Average Rating,Binding,Bookshelves,Borrowed,Date Added,Date Read,Date Started,Entry,Exclusive Shelf,Language,My Rating,Number of Pages,Original Publication Year,Scheduled,Series,Series Id,Title,Work Id
34527,Terry Pratchett,1654,4.27,Paperback,"borrowed, elsewhere",True,2016/05/22,,,19,elsewhere,,0,416,1996,,Discworld,40650,Feet of Clay,3312754
597033,Terry Pratchett,1654,4.03,Mass Market Paperback,"borrowed, elsewhere",True,2016/05/12,,,16,elsewhere,en,0,378,1994,,Discworld,40650,Soul Music,1107935
618221,Terry Pratchett,1654,3.92,Paperback,read,False,2016/05/12,2017/12/23,2017/09/10,10,read,en,5,332,1990,,Discworld,40650,Moving Pictures,1229354
797189,Terry Pratchett,1654,4.22,Paperback,"borrowed, elsewhere",True,2016/05/12,,,20,elsewhere,en,0,445,1996,,Discworld,40650,Hogfather,583655
802929,Terry Pratchett,1654,4.07,Paperback,"borrowed, elsewhere",True,2016/05/12,,,18,elsewhere,en,0,381,1995,,Discworld,40650,Maskerade,968513
833422,Terry Pratchett,1654,4.01,Mass Market Paperback,read,False,2017/09/26,2018/04/27,2018/04/22,3,read,en,4,283,1987,,Discworld,40650,Equal Rites,583611
833424,Terry Pratchett,1654,4.28,Paperback,"2018, borrowed, elsewhere",True,2016/05/12,,,11,elsewhere,en,0,287,1991,2018,Discworld,40650,Reaper Man,1796454
833427,Terry Pratchett,1654,4.21,Paperback,"2018, borrowed, pending",True,2016/01/18,,,12,pending,en,0,288,1991,2018,Discworld,40650,Witches Abroad,929672
833444,Terry Pratchett,1654,4.23,Paperback,read,False,2017/05/24,2018/01/14,2018/01/05,4,read,,5,320,1987,,Discworld,40650,Mort,1857065
"""), index_col=0, parse_dates=['Date Read', 'Date Added'])

    # one per year, already read this year
    eq_([ (date, df.loc[ix].Title) for date, ix in reading.scheduling._schedule(df, {
        'series': 'Discworld$',
    }, date=datetime.date(2018, 6, 4))], [
        ('2019-01-01', 'Reaper Man'),
        ('2020-01-01', 'Witches Abroad'),
        ('2021-01-01', 'Soul Music'),
        ('2022-01-01', 'Maskerade'),
        ('2023-01-01', 'Feet of Clay'),
        ('2024-01-01', 'Hogfather'),
    ])

    eq_([ (date, df.loc[ix].Title) for date, ix in reading.scheduling._schedule(df, {
        'series': 'Discworld$',
        'per_year': 4,
    }, date=datetime.date(2018, 6, 4))], [
        ('2018-07-01', 'Reaper Man'),
        ('2018-10-01', 'Witches Abroad'),
        ('2019-01-01', 'Soul Music'),
        ('2019-04-01', 'Maskerade'),
        ('2019-07-01', 'Feet of Clay'),
        ('2019-10-01', 'Hogfather'),
    ])

