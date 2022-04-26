# vim: ts=4 : sw=4 : et

import pytest

import reading.series
from reading.series import _lookup_series_id, interesting


def test_interesting():
    assert interesting("1", {"Entries": ["1", "2", "3"]})
    assert not interesting("1", {"Entries": ["1"]})
    assert not interesting("1|2", {"Entries": ["1", "2"]})


def test__lookup_series_id(collection):
    c = collection("2019-12-04")

    # FIXME check the exception message?
    with pytest.raises(ValueError):
        _lookup_series_id(c.df, ("_" * 100))

    with pytest.raises(ValueError):
        _lookup_series_id(c.df, "e")


def test_ignore():
    assert not reading.series.ignore(1)
    assert reading.series.ignore(55486)
