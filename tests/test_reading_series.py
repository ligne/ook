# vim: ts=4 : sw=4 : et

from nose.tools import *
from xml.etree import ElementTree

import reading.series
from reading.series import _parse_entries, _get_entry, interesting


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
    eq_(reading.series.ignore(123), True)

