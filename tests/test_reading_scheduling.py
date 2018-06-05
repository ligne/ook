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
    df = pd.DataFrame(index=range(10))
    it = reading.scheduling._allocate(df, 2018, per_year=4, skip=3)
    eq_([ d for (d, ix) in itertools.islice(it, 5)], [
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


    # missing publication year
    df = pd.read_csv(StringIO("""
Book Id,Author,Author Id,Average Rating,Binding,Bookshelves,Borrowed,Date Added,Date Read,Date Started,Entry,Exclusive Shelf,Language,My Rating,Number of Pages,Original Publication Year,Scheduled,Series,Series Id,Title,Work Id
159435,Honoré de Balzac,228089,4.00,Mass Market Paperback,"2018, borrowed, pending",True,2016/05/23,,,,pending,fr,0,,1832,2018,,,Le Colonel Chabert : suivi de trois nouvelles,23642267
34674970,Honoré de Balzac,228089,0.0,Paperback,pending,False,2017/03/24,,,,pending,fr,0,381,,,,,L'illustre Gaudissart / Z. Marcas / Gaudissart II / Les comédiens sans le savoir / Melmoth réconcilié,55846262
"""), index_col=0, parse_dates=['Date Read', 'Date Added'])

    eq_([ (date, df.loc[ix].Title) for date, ix in reading.scheduling._schedule(df, {
        'author': 'Honoré de Balzac',
    }, date=datetime.date(2018, 6, 4))], [
        ('2018-01-01', 'Le Colonel Chabert : suivi de trois nouvelles'),
        ('2019-01-01', 'L\'illustre Gaudissart / Z. Marcas / Gaudissart II / Les comédiens sans le savoir / Melmoth réconcilié'),
    ])


    df = pd.read_csv(StringIO("""
Book Id,Author,Author Id,Average Rating,Binding,Bookshelves,Borrowed,Date Added,Date Read,Date Started,Entry,Exclusive Shelf,Language,My Rating,Number of Pages,Original Publication Year,Scheduled,Series,Series Id,Title,Work Id
366649,Émile Zola,4750,3.90,Paperback,"2018, pending",False,2017/06/20,,,3,pending,fr,0,384,1873,2018,Les Rougon-Macquart,40441,Le Ventre de Paris,10242
816920,Émile Zola,4750,3.84,Mass Market Paperback,ebooks,False,2016/11/24,,,9,ebooks,,0,,1880,,Les Rougon-Macquart,40441,Nana,89633
816921,Émile Zola,4750,4.06,Mass Market Paperback,"borrowed, elsewhere",True,2016/05/22,,,7,elsewhere,fr,0,517,1877,,Les Rougon-Macquart,40441,L'Assommoir,741363
816926,Émile Zola,4750,3.71,Mass Market Paperback,pending,False,2016/05/20,,,,pending,fr,0,317,1867,,,,Thérèse Raquin,1656117
956703,Émile Zola,4750,3.90,Paperback,ebooks,False,2016/11/24,,,10,ebooks,fr,0,510,1882,,Les Rougon-Macquart,40441,Pot-Bouille,110658
1312303,Émile Zola,4750,3.89,Mass Market Paperback,"2019, ebooks",False,2016/11/24,,,4,ebooks,fr,0,480,1874,2019,Les Rougon-Macquart,40441,La Conquête de Plassans,803050
1367035,Émile Zola,4750,3.62,Mass Market Paperback,ebooks,False,2016/11/24,,,8,ebooks,fr,0,370,1877,,Les Rougon-Macquart,40441,Une Page d'amour,1776975
1367070,Émile Zola,4750,3.68,Paperback,ebooks,False,2016/11/24,,,6,ebooks,fr,0,453,1876,,Les Rougon-Macquart,40441,Son Excellence Eugène Rougon,1356899
3071647,Émile Zola,4750,3.63,Mass Market Paperback,pending,False,2017/08/31,,,5,pending,,0,512,1875,,Les Rougon-Macquart,40441,La Faute de l'abbé Mouret,941617
20636970,Émile Zola,4750,3.84,Paperback,read,False,2017/02/07,2018/03/14,2017/12/28,2,read,fr,3,380,1872,,Les Rougon-Macquart,40441,La Curée,839934
"""), index_col=0, parse_dates=['Date Read', 'Date Added'])

    # series sorted numerically
    eq_([ (date, int(df.loc[ix].Entry), df.loc[ix].Title) for date, ix in reading.scheduling._schedule(df, {
        'series': 'Rougon-Macquart',
    }, date=datetime.date(2018, 6, 4))], [
        ('2019-01-01', 3, 'Le Ventre de Paris'),
        ('2020-01-01', 4, 'La Conquête de Plassans'),
        ('2021-01-01', 5, "La Faute de l'abbé Mouret"),
        ('2022-01-01', 6, 'Son Excellence Eugène Rougon'),
        ('2023-01-01', 7, "L'Assommoir"),
        ('2024-01-01', 8, "Une Page d'amour"),
        ('2025-01-01', 9, 'Nana'),
        ('2026-01-01', 10, 'Pot-Bouille'),
    ])

    # force to schedule this year even if i've already read one
    eq_([ (date, int(df.loc[ix].Entry), df.loc[ix].Title) for date, ix in reading.scheduling._schedule(df, {
        'series': 'Rougon-Macquart',
        'force': 2018
    }, date=datetime.date(2018, 6, 4))], [
        ('2018-01-01', 3, 'Le Ventre de Paris'),
        ('2019-01-01', 4, 'La Conquête de Plassans'),
        ('2020-01-01', 5, "La Faute de l'abbé Mouret"),
        ('2021-01-01', 6, 'Son Excellence Eugène Rougon'),
        ('2022-01-01', 7, "L'Assommoir"),
        ('2023-01-01', 8, "Une Page d'amour"),
        ('2024-01-01', 9, 'Nana'),
        ('2025-01-01', 10, 'Pot-Bouille'),
    ])

