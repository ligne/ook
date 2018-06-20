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
        'Author',
        'Title',
        'Shelf',
        'Category',
        'Series',
        'Entry',
        'Language',
        'Pages',

        'Scheduled',
        'Added',
        'Started',
        'Read',

        'Author Id',
        'Series Id',

        'Binding',
        'Published',
        'Work',

        'Rating',
        'AvgRating',

        'Borrowed',
    ]))

    eq_(set(df.Category.values), set([
        'novels',
        'short-stories',
        'non-fiction',
        'graphic',
        np.nan
    ]))

#     eq_(list(zip(df.columns, df.dtypes)), [
#     ])

    b = df.loc[2366570]  # Les Chouans

    # timestamp columns are ok
    eq_(b.Added.strftime('%F'), '2016-04-18')
    eq_(b.Started.strftime('%F'), '2016-09-08')
    eq_(b.Read.strftime('%F'), '2016-11-06')
    eq_(b.Published, 1829.)  # FIXME pandas can't do very old dates...

    b = df.loc[8861500]  # The Dain Curse
    # scheduled is a datetime
    eq_(b.Scheduled.year, 2018)
    eq_(b.Scheduled.strftime('%F'), '2018-01-01')

    b = df.loc[28595808]  # The McCabe Reader
    # missing publication year
    ok_(np.isnan(b.Published))


def test__get_kindle_books():
    # FIXME use a test csv
    df = reading.collection._get_kindle_books()

    eq_(sorted(df.columns), sorted([
        'Author',
        'Binding',
        'Borrowed',
        'Category',
        'Added',
        'Shelf',
        'Language',
        'Pages',
        'Title',
        'Words',
    ]))

    eq_(df.Binding.unique(), ['ebook'])
    eq_(df.Borrowed.unique(), [False])
    eq_(df.Shelf.unique(), ['kindle'])

    eq_(set(df.Category.values), set([
        'articles',
        'non-fiction',
        'novels',
        'short-stories',
    ]))

#     eq_(list(zip(df.columns, df.dtypes)), [
#     ])

    eq_(df[df.Author == 'Edith Birkhead'].Added.dt.strftime('%F').values[0], '2013-02-06', 'Added is the correct datetime')

    # author field is never null
    # FIXME do we actually care?
    eq_(len(df[df.Author.isnull()]), 0)

    # filenames as the index
    # FIXME
    #eq_(list(df.index[0:3]), ['_0', '_1', '_2'])

