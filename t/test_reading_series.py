# vim: ts=4 : sw=4 : et

import pytest

import pandas as pd

import reading.series
from reading.series import _parse_entries, _get_entry, interesting
from reading.series import _lookup_series_id
from reading.series import Series


def test__get_entry():
    assert _get_entry('1') == 1
    assert _get_entry('3') == 3
    assert _get_entry('1.1') is None
    assert _get_entry('1 of 2') == 1


def test__parse_entries():
    assert _parse_entries('1') == [1]
    assert _parse_entries('1-2') == [1, 2]
    assert _parse_entries('2-4') == [2, 3, 4]
    assert _parse_entries('2-4 ') == [2, 3, 4]
    assert _parse_entries('0') == [0]
    assert _parse_entries('0-2') == [0, 1, 2]

    assert _parse_entries('1, 2') == [1, 2]
    assert _parse_entries('1,2') == [1, 2]
    assert _parse_entries('1 & 2') == [1, 2]
    assert _parse_entries('1&2') == [1, 2]
    assert _parse_entries('1 & 3') == [1, 3]
    assert _parse_entries('1, 2 & 4') == [1, 2, 4]
    assert _parse_entries('1, 2, 4') == [1, 2, 4]
    assert _parse_entries('1-3 , 5') == [1, 2, 3, 5]
    assert _parse_entries('1-3 & 5') == [1, 2, 3, 5]
    assert _parse_entries('1-4, 6-7') == [1, 2, 3, 4, 6, 7]

    assert _parse_entries(None) == []
    assert _parse_entries('') == []
    assert _parse_entries(123) == []
    assert _parse_entries(1.3) == []

    # extra cruft
    assert _parse_entries('1-3 omnibus') == [1, 2, 3]
    assert _parse_entries('1 part 1') == [1]
    assert _parse_entries('1.3 (Monarch of the Glen)') == []
    assert _parse_entries('1 of 2') == [1]
    assert _parse_entries('2 of 2') == [2]
    assert _parse_entries('I') == []
    assert _parse_entries('3 pt. 2') == [3]
    assert _parse_entries('11B') == [11]
    assert _parse_entries('1, part 2 of 2') == [1]
    assert _parse_entries('2 (1/2)') == [2]
    assert _parse_entries('3 part 2/2') == [3]
    assert _parse_entries('Short Stories') == []

    # dotted entries
    assert _parse_entries('0.5') == []
    assert _parse_entries('0.5, 0.6') == []
    assert _parse_entries('0.5-0.6') == []
    assert _parse_entries('1-3, 3.1') == [1, 2, 3]
    assert _parse_entries('4, 5.2 & 13 ') == [4, 13]


def test_interesting():
    assert interesting('1', {
        'Entries': ['1', '2', '3']
    })

    assert not interesting('1', {
        'Entries': ['1']
    })

    assert not interesting('1-2', {
        'Entries': ['1', '2']
    })


def test__lookup_series_id(collection):
    c = collection("2019-12-04")

    # FIXME check the exception message?
    with pytest.raises(ValueError):
        _lookup_series_id(c.df, ('_' * 100))

    with pytest.raises(ValueError):
        _lookup_series_id(c.df, 'e')


def test_ignore():
    assert not reading.series.ignore(1)
    assert reading.series.ignore(55486)


################################################################################

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


@pytest.mark.xfail
def test_duplicate_warning():
    """A warning should be issued if there are duplicate books in a series."""
    # but there aren't any duplicates at the moment
    with pytest.warns(UserWarning):
        Series(author='Iain Banks')


def test_series_last_read(collection):
    c = collection("2019-12-04", fixes=False)

    s = Series(author='Hašek', df=c.df)
    assert s.last_read() is None, 'Never read'

    s = Series(author='Vonnegut', df=c.df)
    assert s.last_read().date() == pd.Timestamp('today').date(), 'Currently reading'

    s = Series(author='Murakami', df=c.df)
    assert str(s.last_read().date()) == '2019-08-27', 'Previously read'

