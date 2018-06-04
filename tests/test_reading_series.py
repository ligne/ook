# vim: ts=4 : sw=4 : et

import nose
from xml.etree import ElementTree

import reading.series

def test__parse_entries():
    nose.tools.assert_equals(reading.series._parse_entries('1'), [1])
    nose.tools.assert_equals(reading.series._parse_entries('1-2'), [1,2])
    nose.tools.assert_equals(reading.series._parse_entries('2-4'), [2,3,4])
    nose.tools.assert_equals(reading.series._parse_entries('2-4 '), [2,3,4])

    # extraneous data
    # '1-2, 4'
    # None


def test_ignore():
    nose.tools.assert_equals(reading.series.ignore(1), False)
    nose.tools.assert_equals(reading.series.ignore(123), True)

