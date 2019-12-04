# vim: ts=4 : sw=4 : et

import pytest

from nose.tools import eq_, ok_

from reading.collection import Collection

import reading.series
from reading.series import _parse_entries, _get_entry, interesting
from reading.series import Series


def test__get_entry():
    eq_(_get_entry('1'), 1)
    eq_(_get_entry('3'), 3)
    eq_(_get_entry('1.1'), None)
    eq_(_get_entry('1 of 2'), 1)


def test__parse_entries():
    eq_(_parse_entries('1'), [1])
    eq_(_parse_entries('1-2'), [1,2])
    eq_(_parse_entries('2-4'), [2,3,4])
    eq_(_parse_entries('2-4 '), [2,3,4])
    eq_(_parse_entries('0'), [0])
    eq_(_parse_entries('0-2'), [0,1,2])

    eq_(_parse_entries('1, 2'), [1,2])
    eq_(_parse_entries('1,2'), [1,2])
    eq_(_parse_entries('1 & 2'), [1,2])
    eq_(_parse_entries('1&2'), [1,2])
    eq_(_parse_entries('1 & 3'), [1,3])
    eq_(_parse_entries('1, 2 & 4'), [1,2,4])
    eq_(_parse_entries('1, 2, 4'), [1,2,4])
    eq_(_parse_entries('1-3 , 5'), [1,2,3,5])
    eq_(_parse_entries('1-3 & 5'), [1,2,3,5])
    eq_(_parse_entries('1-4, 6-7'), [1,2,3,4,6,7])

    eq_(_parse_entries(None), [])
    eq_(_parse_entries(''), [])
    eq_(_parse_entries(123), [])
    eq_(_parse_entries(1.3), [])

    # extra cruft
    eq_(_parse_entries('1-3 omnibus'), [1,2,3])
    eq_(_parse_entries('1 part 1'), [1])
    eq_(_parse_entries('1.3 (Monarch of the Glen)'), [])
    eq_(_parse_entries('1 of 2'), [1])
    eq_(_parse_entries('2 of 2'), [2])
    eq_(_parse_entries('I'), [])
    eq_(_parse_entries('3 pt. 2'), [3])
    eq_(_parse_entries('11B'), [11])
    eq_(_parse_entries('1, part 2 of 2'), [1])
    eq_(_parse_entries('2 (1/2)'), [2])
    eq_(_parse_entries('3 part 2/2'), [3])
    eq_(_parse_entries('Short Stories'), [])

    # dotted entries
    eq_(_parse_entries('0.5'), [])
    eq_(_parse_entries('0.5, 0.6'), [])
    eq_(_parse_entries('0.5-0.6'), [])
    eq_(_parse_entries('1-3, 3.1'), [1,2,3])
    eq_(_parse_entries('4, 5.2 & 13 '), [4, 13])


def test_interesting():
    eq_(interesting('1', {
        'Entries': [ '1', '2', '3' ]
    }), True)

    eq_(interesting('1', {
        'Entries': ['1']
    }), False)

    eq_(interesting('1-2', {
        'Entries': ['1', '2']
    }), False)


def test_ignore():
    eq_(reading.series.ignore(1), False)
    eq_(reading.series.ignore(55486), True)


################################################################################

def _get_collection():
    return Collection(gr_csv='t/data/goodreads-2019-12-04.csv')


def test_series():
    # needs at least *something* to go on
    with pytest.raises(ValueError):
        Series()

    # by author name
    s = Series(author='Beauvoir')
    assert s, 'Created a series from an author'
    assert s.label == 'Beauvoir'
    assert s.order == 'published', 'Authors are read in published order by default'
    assert s.missing == 'ignore', 'Authors have no missing books to ignore'

    # warning when there are duplicates
    with pytest.warns(UserWarning):
        Series(author='Iain Banks')

    # by series name
    s = Series(series='Culture')
    assert s, 'Created a series from a name'
    assert s.label == 'Culture'
    assert s.order == 'series', 'Series are read in order'
    assert s.missing == 'ignore'

    # by SeriesID
    s = Series(series_id=49118)
    assert s, 'Created a series from an ID'
    assert s.label == 'Culture'
    assert s.order == 'series', 'Series are read in order'
    assert s.missing == 'ignore'

    # FIXME check these last two have the same results

    # series can have multiple authors
    s = Series(series='Spirou')
    assert len(set(s.df.Author)) > 1

    # settings
    s = Series(series='Culture', settings={
        'order': 'published',
    })
    assert s.order == 'published', 'Can override the order of series'
    assert s.missing == 'ignore', 'By default ignore missing books from series'

    # FIXME also check .missing behaviour

