# vim: ts=4 : sw=4 : et

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


c = Collection.from_dir("t/data/2019-12-04")

# an unread book
BOOK_UNREAD = c.df.loc[9556]
assert BOOK_UNREAD.Title == "The Elephant Vanishes"
assert BOOK_UNREAD.Shelf == "pending"
# null values do not equal themselves
assert pd.isna(BOOK_UNREAD.Series), "There's a null value"

# a book with a modified field
BOOK_MODIFIED = BOOK_UNREAD.replace(
    "The Elephant Vanishes",
    "One Of Our Elephants Is Missing",
)
assert not BOOK_MODIFIED.equals(BOOK_UNREAD), "They're not equal"
assert BOOK_MODIFIED.Title != BOOK_UNREAD.Title, "The title is changed"
assert BOOK_MODIFIED.Author == BOOK_UNREAD.Author, "The author has not changed"

# a book moving from unread -> reading -> read
BOOK_PENDING = c.df.loc[12021]
BOOK_CURRENT = c.df.loc[12022]
BOOK_READ = c.df.loc[12023]
assert BOOK_PENDING.Title == BOOK_CURRENT.Title == BOOK_READ.Title == "The Crow Road"
assert BOOK_PENDING.Shelf == "pending"
assert BOOK_CURRENT.Shelf == "currently-reading"
assert BOOK_READ.Shelf == "read"


################################################################################


def test_changed_field() -> None:
    value = BOOK_UNREAD.Author
    assert not pd.isna(value), "Got a non-null value"

    na_value = BOOK_UNREAD.Series
    assert pd.isna(na_value), "Got a null value"

    name = "blah"  # the exact name doesn't really matter

    assert ChangedField(name, old=na_value, new=na_value).direction == ChangeDirection.MISSING
    assert ChangedField(name, old=value, new=na_value).direction == ChangeDirection.UNSET
    assert ChangedField(name, old=na_value, new=value).direction == ChangeDirection.SET
    assert ChangedField(name, old=value, new=value).direction == ChangeDirection.UNCHANGED
    assert ChangedField(name, old=value, new=value.lower()).direction == ChangeDirection.CHANGED


################################################################################


def test_change_added() -> None:
    """Added a book."""

    old = None
    new = BOOK_UNREAD

    change = Change(old, new)

    assert change.is_added is True
    assert change.is_removed is False
    assert change.is_started is False
    assert change.is_finished is False
    assert change.is_modified is False  # FIXME or should that be true?

    assert change.event == ChangeEvent.ADDED

    assert change.book.equals(new), "the book property works when old is missing"


def test_change_removed() -> None:
    """Removed a book."""

    old = BOOK_UNREAD
    new = None

    change = Change(old, new)

    assert change.is_added is False
    assert change.is_removed is True
    assert change.is_started is False
    assert change.is_finished is False
    assert change.is_modified is False  # FIXME or should that be true?

    assert change.event == ChangeEvent.REMOVED

    assert change.book.equals(old), "the book property works when new is missing"


def test_change_started() -> None:
    """Existing book that's just been started."""

    old = BOOK_PENDING
    new = BOOK_CURRENT

    assert old.Title == new.Title == "The Crow Road"

    change = Change(old, new)

    assert change.is_added is False
    assert change.is_removed is False
    assert change.is_started is True
    assert change.is_finished is False
    assert change.is_modified is True

    assert change.event == ChangeEvent.STARTED


def test_change_added_and_started() -> None:
    """Newly-added book that's also just been started: started takes precedent."""

    old = None
    new = BOOK_CURRENT

    assert new.Title == "The Crow Road"
    assert new.Shelf == "currently-reading"

    change = Change(old, new)

    assert change.is_added is True
    assert change.is_removed is False
    assert change.is_started is True
    assert change.is_finished is False
    assert change.is_modified is False  # FIXME or should that be true?

    assert change.event == ChangeEvent.STARTED


def test_change_already_started() -> None:
    """It's only started the first time."""

    old = BOOK_CURRENT
    new = BOOK_CURRENT

    assert new.Title == old.Title == "The Crow Road"
    assert new.Shelf == old.Shelf == "currently-reading"

    change = Change(old, new)

    assert change.is_added is False
    assert change.is_removed is False
    assert change.is_started is False
    assert change.is_finished is False
    assert change.is_modified is False  # this is definitely false

    assert change.event == ChangeEvent.UNMODIFIED


def test_change_finished() -> None:
    """Existing book that's just been finished."""

    old = BOOK_CURRENT
    new = BOOK_READ

    assert old.Title == new.Title == "The Crow Road"

    change = Change(old, new)

    assert change.is_added is False
    assert change.is_removed is False
    assert change.is_started is False
    assert change.is_finished is True
    assert change.is_modified is True

    assert change.event == ChangeEvent.FINISHED


def test_change_added_and_finished() -> None:
    """Newly-added book that's also just been finished: finished takes precedent."""

    old = None
    new = BOOK_READ

    assert new.Title == "The Crow Road"
    assert new.Shelf == "read"

    change = Change(old, new)

    assert change.is_added is True
    assert change.is_removed is False
    assert change.is_started is False
    assert change.is_finished is True
    assert change.is_modified is False  # FIXME or should that be true?

    assert change.event == ChangeEvent.FINISHED


def test_change_already_finished() -> None:
    """It's only finished the first time."""

    old = BOOK_READ
    new = BOOK_READ

    assert new.Title == old.Title == "The Crow Road"
    assert new.Shelf == old.Shelf == "read"

    change = Change(old, new)

    assert change.is_added is False
    assert change.is_removed is False
    assert change.is_started is False
    assert change.is_finished is False
    assert change.is_modified is False  # this is definitely false

    assert change.event == ChangeEvent.UNMODIFIED


def test_change_identical() -> None:
    """Nothing has changed."""

    old = BOOK_UNREAD
    new = BOOK_UNREAD

    change = Change(old, new)

    assert change.old is change.new, "Old and new versions should be identical"

    # null values do not equal themselves
    assert pd.isna(new.Series), "There's a null value"

    assert change.is_added is False
    assert change.is_removed is False
    assert change.is_started is False
    assert change.is_finished is False
    assert change.is_modified is False


def test_change_modified() -> None:
    """A field has changed in an existing book."""

    old = BOOK_UNREAD
    new = BOOK_MODIFIED

    assert old.Title == "The Elephant Vanishes"
    assert new.Title == "One Of Our Elephants Is Missing"

    change = Change(old, new)

    assert change.is_modified is True


################################################################################


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
