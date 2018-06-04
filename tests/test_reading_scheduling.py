# vim: ts=4 : sw=4 : et

import nose
from nose.tools import *

import pandas as pd
import itertools

import reading.scheduling


def test__dates():

    # one a year
    it = reading.scheduling._dates(2018)
    eq_(list(itertools.islice(it, 5)), [
        '2018-01-01',
        '2019-01-01',
        '2020-01-01',
        '2021-01-01',
        '2022-01-01',
    ])

    # several a year
    it = reading.scheduling._dates(2018, per_year=4)
    eq_(list(itertools.islice(it, 5)), [
        '2018-01-01',
        '2018-04-01',
        '2018-07-01',
        '2018-10-01',
        '2019-01-01',
    ])

    # several a year
    it = reading.scheduling._dates(2018, per_year=3)
    eq_(list(itertools.islice(it, 5)), [
        '2018-01-01',
        '2018-05-01',
        '2018-09-01',
        '2019-01-01',
        '2019-05-01',
    ])

    # offset into the year
    it = reading.scheduling._dates(2018, offset=10)
    eq_(list(itertools.islice(it, 5)), [
        '2018-10-01',
        '2019-10-01',
        '2020-10-01',
        '2021-10-01',
        '2022-10-01',
    ])

    # multiple, offset
    it = reading.scheduling._dates(2018, per_year=2, offset=2)
    eq_(list(itertools.islice(it, 5)), [
        '2018-02-01',
        '2018-08-01',
        '2019-02-01',
        '2019-08-01',
        '2020-02-01',
    ])

    # only one remaining this year
    it = reading.scheduling._dates(2018, per_year=4, skip=3)
    eq_(list(itertools.islice(it, 5)), [
        '2018-10-01',
        '2019-01-01',
        '2019-04-01',
        '2019-07-01',
        '2019-10-01',
    ])

