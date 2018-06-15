# vim: ts=4 : sw=4 : et

from nose.tools import *

import pandas as pd
import numpy as np
from io import StringIO

import reading.collection


def test__get_gr_books():
    # FIXME use a test csv
    df = reading.collection._get_gr_books()

    assert_equals(sorted(df.columns), sorted([
        'Date Added', #'Added',
        'Author',
        'Author Id',
        'AvgRating',
        'Binding',
        'Borrowed',
        'Category',
        'Entry',
        'Language',
        'Pages',
        'Original Publication Year', #'Published',
        'My Rating', #'Rating',
        'Date Read', #'Read',
        'Scheduled',
        'Series',
        'Series Id',
        'Exclusive Shelf', #'Shelf',
        'Date Started', #'Started',
        'Title',
        'Work',
    ]))

    eq_(set(df.Category.values), set([
        'novel',
        'short-stories',
        'non-fiction',
        'graphic',
        np.nan
    ]))

#     eq_(list(zip(df.columns, df.dtypes)), [
#     ])

    b = df.loc[2366570]  # Les Chouans

    # timestamp columns are ok
    eq_(b['Date Added'].strftime('%F'), '2016-04-18') #eq_(b.Added.strftime('%F'), '2016-04-18')
    eq_(b['Date Started'].strftime('%F'), '2016-09-08') #eq_(b.Started.strftime('%F'), '2016-09-08')
    eq_(b['Date Read'].strftime('%F'), '2016-11-06') #eq_(b.Read.strftime('%F'), '2016-11-06')
    eq_(b['Original Publication Year'], 1829.) #eq_(b.Published, 1829.)  # FIXME pandas can't do very old dates...

    b = df.loc[8861500]  # The Dain Curse
    # scheduled is a datetime
    eq_(b.Scheduled.year, 2018)
    eq_(b.Scheduled.strftime('%F'), '2018-01-01')

    b = df.loc[28595808]  # The McCabe Reader
    # missing publication year
    ok_(np.isnan(b['Original Publication Year'])) #ok_(np.isnan(b.Published))


def test__get_kindle_books():
    # FIXME use a test csv
    df = reading.collection._get_kindle_books()

    eq_(set(df.columns), set([
        'Author',
        'Binding',
        'Borrowed',
        'Category',
        'Added',
        'Shelf',
        'Language',
        'Pages',
        'Title',
    ]))

    eq_(df.Binding.unique(), ['ebook'])
    eq_(df.Borrowed.unique(), [False])
    eq_(df.Shelf.unique(), ['kindle'])

#     eq_(list(zip(df.columns, df.dtypes)), [
#     ])

    eq_(df[df.Author == 'Edith Birkhead'].Added.dt.strftime('%F').values[0], '2013-02-06', 'Added is the correct datetime')

    # author field is never null
    # FIXME do we actually care?
    eq_(len(df[df.Author.isnull()]), 0)

    # set an index that won't clash with goodreads's.
    eq_(list(df.index[0:3]), ['_0', '_1', '_2'])

