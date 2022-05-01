# vim: ts=4 : sw=4 : et

from reading.series import interesting


def test_interesting():
    assert interesting("1", {"Entries": ["1", "2", "3"]})
    assert not interesting("1", {"Entries": ["1"]})
    assert not interesting("1|2", {"Entries": ["1", "2"]})
