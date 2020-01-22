# vim: ts=4 : sw=4 : et

import numpy as np

import reading.collection
from reading.collection import Collection


def _get_collection():
    return Collection(gr_csv='t/data/goodreads-2019-12-04.csv', fixes=False)


def test__get_gr_books():
    c = _get_collection()
    df = c.df

    assert sorted(df.columns) == sorted([
        'Author',
        'Title',
        'Shelf',
        'Category',
        'Series',
        'Entry',
        'Language',
        'Pages',
        'Words',

        'Scheduled',
        'Added',
        'Started',
        'Read',

        'AuthorId',
        'SeriesId',

        'Gender',
        'Nationality',

        'Binding',
        'Published',
        'Work',

        'Rating',
        'AvgRating',

        'Borrowed',
    ])

    assert set(df.Category) == set([
        'novels',
        'short-stories',
        'non-fiction',
        'graphic',
        np.nan
    ])

#     eq_(list(zip(df.columns, df.dtypes)), [
#     ])

    b = df.loc[2366570]  # Les Chouans

    # timestamp columns are ok
    assert str(b.Added.date()) == '2016-04-18'
    assert str(b.Started.date()) == '2016-09-08'
    assert str(b.Read.date()) == '2016-11-06'
    assert b.Published == 1829  # pandas can't do very old dates...

    b = df.loc[3071647]  # La faute de l'abbé Mouret
    assert str(b.Scheduled.date()) == '2020-01-01', 'Scheduled column is a timestamp'

    b = df.loc[28595808]  # The McCabe Reader
    # missing publication year
    assert np.isnan(b.Published)


def test__get_kindle_books():
    # FIXME use a test csv
    df = reading.collection._get_kindle_books()

    assert list(df.columns) == [
        'Author',
        'Title',
        'Shelf',
        'Category',
        'Language',
        'Added',
        'Binding',
        'Words',
        'Borrowed',
        'Pages',
    ]

    assert set(df.Binding) == {'ebook'}, 'ebook binding is always ebook'
    assert set(df.Borrowed) == {False}, 'ebooks are never borrowed'
    assert set(df.Shelf) == {'kindle'}, 'ebook shelf is always kindle'

    assert set(df.Category) == set([
        'articles',
        'non-fiction',
        'novels',
        'short-stories',
    ])

#     eq_(list(zip(df.columns, df.dtypes)), [
#     ])

    b = df.loc['non-fiction/pg14154.mobi']  # A Tale of Terror

    assert str(b.Added.date()) == '2013-02-06', 'Added is sensible'

    # FIXME do we actually care?
    assert len(df[df.Author.isnull()]) == 0, 'Every ebook has an author'


def test_collection():
    c = Collection()
    assert c.df.equals(Collection().df), 'Same collection is the same'


def test__process_fixes():
    assert not reading.collection._process_fixes({}), 'No fixes to apply'


