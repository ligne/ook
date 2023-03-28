# vim: ts=4 : sw=4 : et

from typing import Callable

import pandas as pd

from reading.collection import Collection
from reading.compare import (
    Change,
    ChangedField,
    ChangeDirection,
    ChangeEvent,
    _added,
    _changed,
    _finished,
    _removed,
    _started,
)


CollectionFixture = Callable[[str], Collection]

################################################################################


def test_changed_field(collection: CollectionFixture) -> None:
    c = collection("2019-12-04")
    book = c.df.iloc[0]

    value = book.Author
    assert not pd.isna(value), "Got a non-null value"

    na_value = book.Series
    assert pd.isna(na_value), "Got a null value"

    name = "blah"  # the exact name doesn't really matter

    assert ChangedField(name, old=na_value, new=na_value).direction == ChangeDirection.MISSING
    assert ChangedField(name, old=value, new=na_value).direction == ChangeDirection.UNSET
    assert ChangedField(name, old=na_value, new=value).direction == ChangeDirection.SET
    assert ChangedField(name, old=value, new=value).direction == ChangeDirection.UNCHANGED
    assert ChangedField(name, old=value, new=value.lower()).direction == ChangeDirection.CHANGED


################################################################################


def test_change_added(collection: CollectionFixture) -> None:
    """Added a book."""

    c = collection("2019-12-04")

    old = None
    new = c.df.iloc[0]

    change = Change(old, new)

    assert change.is_added is True
    assert change.is_removed is False
    assert change.is_started is False
    assert change.is_finished is False
    assert change.is_modified is False  # FIXME or should that be true?

    assert change.event == ChangeEvent.ADDED

    assert change.book.equals(new), "the book property works when old is missing"


def test_change_removed(collection: CollectionFixture) -> None:
    """Removed a book."""

    c = collection("2019-12-04")

    old = c.df.iloc[0]
    new = None

    change = Change(old, new)

    assert change.is_added is False
    assert change.is_removed is True
    assert change.is_started is False
    assert change.is_finished is False
    assert change.is_modified is False  # FIXME or should that be true?

    assert change.event == ChangeEvent.REMOVED

    assert change.book.equals(old), "the book property works when new is missing"


def test_change_started(collection: CollectionFixture) -> None:
    """Existing book that's just been started."""

    c = collection("2019-12-04")

    old = c.df.loc[1367070]
    new = c.df.loc[1367071]

    assert old.Title == new.Title == "Son Excellence Eugène Rougon"

    change = Change(old, new)

    assert change.is_added is False
    assert change.is_removed is False
    assert change.is_started is True
    assert change.is_finished is False
    assert change.is_modified is True

    assert change.event == ChangeEvent.STARTED


def test_change_added_and_started(collection: CollectionFixture) -> None:
    """Newly-added book that's also just been started: started takes precedent."""

    c = collection("2019-12-04")

    old = None
    new = c.df.loc[1367071]

    assert new.Title == "Son Excellence Eugène Rougon"
    assert new.Shelf == "currently-reading"

    change = Change(old, new)

    assert change.is_added is True
    assert change.is_removed is False
    assert change.is_started is True
    assert change.is_finished is False
    assert change.is_modified is False  # FIXME or should that be true?

    assert change.event == ChangeEvent.STARTED


def test_change_already_started(collection: CollectionFixture) -> None:
    """It's only started the first time."""

    c = collection("2019-12-04")

    old = c.df.loc[1367071]
    new = old

    assert new.Title == old.Title == "Son Excellence Eugène Rougon"
    assert new.Shelf == old.Shelf == "currently-reading"

    change = Change(old, new)

    assert change.is_added is False
    assert change.is_removed is False
    assert change.is_started is False
    assert change.is_finished is False
    assert change.is_modified is False  # this is definitely false

    assert change.event == ChangeEvent.UNMODIFIED


def test_change_finished(collection: CollectionFixture) -> None:
    """Existing book that's just been finished."""

    c = collection("2019-12-04")

    old = c.df.loc[12021]
    new = c.df.loc[12022]

    assert old.Title == new.Title == "The Crow Road"

    change = Change(old, new)

    assert change.is_added is False
    assert change.is_removed is False
    assert change.is_started is False
    assert change.is_finished is True
    assert change.is_modified is True

    assert change.event == ChangeEvent.FINISHED


def test_change_added_and_finished(collection: CollectionFixture) -> None:
    """Newly-added book that's also just been finished: finished takes precedent."""

    c = collection("2019-12-04")

    old = None
    new = c.df.loc[20636970]

    assert new.Title == "La Curée"
    assert new.Shelf == "read"

    change = Change(old, new)

    assert change.is_added is True
    assert change.is_removed is False
    assert change.is_started is False
    assert change.is_finished is True
    assert change.is_modified is False  # FIXME or should that be true?

    assert change.event == ChangeEvent.FINISHED


def test_change_already_finished(collection: CollectionFixture) -> None:
    """It's only finished the first time."""

    c = collection("2019-12-04")

    old = c.df.loc[20636970]
    new = old

    assert new.Title == old.Title == "La Curée"
    assert new.Shelf == old.Shelf == "read"

    change = Change(old, new)

    assert change.is_added is False
    assert change.is_removed is False
    assert change.is_started is False
    assert change.is_finished is False
    assert change.is_modified is False  # this is definitely false

    assert change.event == ChangeEvent.UNMODIFIED


def test_change_identical(collection: CollectionFixture) -> None:
    """Nothing has changed."""

    c = collection("2019-12-04")

    old = c.df.loc[20636970]
    new = old

    change = Change(old, new)

    assert change.old is change.new, "Old and new versions should be identical"

    # NA does not equal itself
    assert pd.isna(new.Scheduled), "There's a <NA> value"

    assert change.is_added is False
    assert change.is_removed is False
    assert change.is_started is False
    assert change.is_finished is False
    assert change.is_modified is False


def test_change_modified(collection: CollectionFixture) -> None:
    """A field has changed in an existing book."""

    old = c.df.loc[1367070]
    new = old.copy()

    new["Title"] = "New Title"
    assert not old.equals(new), "The old and new books should be different"

    change = Change(old, new)

    assert change.is_modified is True


################################################################################


c = Collection.from_dir("t/data/2019-12-04")
df = c.df.fillna("")


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
