# vim: ts=4 : sw=4 : et

import pandas as pd

from reading.collection import Collection
from reading.compare import _added, _changed, _finished, _removed, _started


c = Collection.from_dir("t/data/2019-12-04")
df = c.df.fillna("")


################################################################################


def test__added() -> None:
    assert (
        _added(df.loc[26570162])
        == """
Added The Monk by Matthew Lewis to shelf 'pending'
  * novels
  * 339 pages
  * Language: en
""".strip()
    ), "Added book"

    assert (
        _added(df.loc[23533039])
        == """
Added Ancillary Mercy by Ann Leckie to shelf 'pending'
  * Imperial Radch series, Book 3
  * novels
  * 330 pages
  * Language: en
""".strip()
    ), "Added book with series"


def test__removed() -> None:
    assert (
        _removed(df.loc[26570162])
        == """
Removed The Monk by Matthew Lewis from shelf 'pending'
""".strip()
    ), "Removed book"


def test__started() -> None:
    assert (
        _started(df.loc[26570162])
        == """
Started The Monk by Matthew Lewis
  * novels
  * 339 pages
  * Language: en
""".strip()
    ), "Started book"


def test__finished() -> None:
    assert (
        _finished(df.loc[491030])
        == """
Finished The Bridge by Iain Banks
  * 2016-07-19 → 2016-08-10 (22 days)
  * 288 pages, 13 pages/day
  * Rating: 4
  * Category: novels
  * Published: 1986
  * Language: en
""".strip()
    ), "Finished book"

    # read in one day
    assert (
        _finished(df.loc[25965499])
        == """
Finished A Few Notes on the Culture by Iain M. Banks
  * 2018-12-31 → 2018-12-31 (0 days)
  * 17 pages, 17 pages/day
  * Rating: 4
  * Category: non-fiction
  * Published: 1994
  * Language: en
""".strip()
    ), "Read in one day"


def test__changed() -> None:
    b1 = df.loc[26570162]

    # FIXME should do nothing if they're both equal?
    assert _changed(b1, b1) is None, "Nothing if the books are the same"

    ###
    b2 = b1.copy()
    b2.Title = b2.Title.lower()

    assert (
        _changed(b1, b2)
        == """
Matthew Lewis, the monk
  * Title changed from 'The Monk'
""".strip()
    ), "Change in title is treated specially"

    ###
    b2 = b1.copy()
    b2.Author = b2.Author.lower()

    assert (
        _changed(b1, b2)
        == """
matthew lewis, The Monk
  * Author changed from 'Matthew Lewis'
""".strip()
    ), "Change in author is treated specially"

    ###
    b2 = b1.copy()
    b2.Shelf = "elsewhere"
    b2.Pages = 426

    assert (
        _changed(b1, b2)
        == """
Matthew Lewis, The Monk
  * Shelf: pending → elsewhere
  * Pages: 339 → 426
""".strip()
    ), "Various other fields changed"

    ###
    b2 = b1.copy()
    b2.Category = None
    b2.Added = pd.Timestamp("2017-12-25")
    b1a = b1.copy()
    b1a.Binding = None

    assert (
        _changed(b1a, b2)
        == """
Matthew Lewis, The Monk
  * Category unset (previously novels)
  * Binding set to Paperback
  * Added: 2017-07-27 → 2017-12-25
""".strip()
    ), "Fields set and unset"

    ###
    b2 = b1.copy()
    b2.Scheduled = pd.Timestamp("2021-01-01")
    b1a = b1.copy()
    b1a.Scheduled = pd.Timestamp("2020-01-01")

    assert (
        _changed(b1, b2)
        == """
Matthew Lewis, The Monk
  * Scheduled for 2021
""".strip()
    ), "Scheduled"

    assert (
        _changed(b2, b1)
        == """
Matthew Lewis, The Monk
  * Unscheduled for 2021
""".strip()
    ), "Unscheduled"

    assert (
        _changed(b1a, b2)
        == """
Matthew Lewis, The Monk
  * Scheduled: 2020 → 2021
""".strip()
    ), "Scheduled year changed"

    ###
    b2 = b1.copy()
    b2.AvgRating += 1.2

    assert _changed(b1, b2) is None, "Changes to the average rating are ignored"
