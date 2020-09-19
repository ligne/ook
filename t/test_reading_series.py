# vim: ts=4 : sw=4 : et

import pytest

import reading.series
from reading.series import _get_entry, _lookup_series_id, _parse_entries, interesting


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
