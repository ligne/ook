# vim: ts=4 : sw=4 : et

from typing import Any

import pandas as pd
import pytest

from reading.collection import Collection
from reading.compare import (
    BookFormatter,
    Change,
    ChangedField,
    ChangeDirection,
    ChangeEvent,
    ChangeStyler,
    FormattedValue,
    ValueFormats,
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


NA_VALUE = BOOK_UNREAD.Series
assert pd.isna(NA_VALUE), "Got a null value"

VALUE = BOOK_UNREAD.Author
assert not pd.isna(VALUE), "Got a non-null value"

CHANGED_VALUE = VALUE.lower()
assert VALUE != CHANGED_VALUE, "Got a changed, non-null value"


@pytest.mark.parametrize(
    "old_value, new_value, direction",
    (
        (NA_VALUE, NA_VALUE, ChangeDirection.MISSING),
        (VALUE, NA_VALUE, ChangeDirection.UNSET),
        (NA_VALUE, VALUE, ChangeDirection.SET),
        (VALUE, VALUE, ChangeDirection.UNCHANGED),
        (VALUE, CHANGED_VALUE, ChangeDirection.CHANGED),
    ),
)
def test_changed_field(old_value: Any, new_value: Any, direction: ChangeDirection) -> None:
    """All the permutations of changed fields."""

    name = "blah"  # the exact name doesn't really matter

    assert ChangedField(name, old=old_value, new=new_value).direction == direction


################################################################################


@pytest.mark.parametrize(
    "change, event, predicates",
    (
        pytest.param(
            Change(old=None, new=BOOK_UNREAD),
            ChangeEvent.ADDED,
            {
                "is_added": True,
            },
            id="Added a book",
        ),
        pytest.param(
            Change(old=BOOK_UNREAD, new=None),
            ChangeEvent.REMOVED,
            {
                "is_removed": True,
            },
            id="Removed a book",
        ),
        pytest.param(
            Change(old=BOOK_PENDING, new=BOOK_CURRENT),
            ChangeEvent.STARTED,
            {
                "is_started": True,
                "is_modified": True,
            },
            id="Existing book that's just been started",
        ),
        pytest.param(
            Change(old=None, new=BOOK_CURRENT),
            ChangeEvent.STARTED,
            {
                "is_added": True,
                "is_started": True,
            },
            id="Newly-added book that's also just been started: started takes precedent",
        ),
        pytest.param(
            Change(old=BOOK_CURRENT, new=BOOK_CURRENT),
            ChangeEvent.UNMODIFIED,
            {},
            id="It's only started the first time",
        ),
        pytest.param(
            Change(old=BOOK_CURRENT, new=BOOK_READ),
            ChangeEvent.FINISHED,
            {
                "is_finished": True,
                "is_modified": True,
            },
            id="Existing book that's just been finished.",
        ),
        pytest.param(
            Change(old=None, new=BOOK_READ),
            ChangeEvent.FINISHED,
            {
                "is_added": True,
                "is_finished": True,
            },
            id="Newly-added book that's also just been finished: finished takes precedent",
        ),
        pytest.param(
            Change(old=BOOK_READ, new=BOOK_READ),
            ChangeEvent.UNMODIFIED,
            {},
            id="It's only finished the first time",
        ),
        pytest.param(
            Change(old=BOOK_UNREAD, new=BOOK_UNREAD),
            ChangeEvent.UNMODIFIED,
            {},
            id="Nothing has changed",
        ),
        pytest.param(
            Change(old=BOOK_UNREAD, new=BOOK_MODIFIED),
            ChangeEvent.MODIFIED,
            {
                "is_modified": True,
            },
            id="A field has changed in an existing book",
        ),
    ),
)
def test_change(change: Change, event: ChangeEvent, predicates: dict[str, bool]) -> None:
    """Basic functionality of the Change class: predicates, event, book accessor."""

    def check_predicates(
        is_added: bool = False,
        is_removed: bool = False,
        is_started: bool = False,
        is_finished: bool = False,
        is_modified: bool = False,
    ) -> None:
        assert change.is_added is is_added
        assert change.is_removed is is_removed
        assert change.is_started is is_started
        assert change.is_finished is is_finished
        # FIXME would it be useful for is_modified also to be true for added/removed books?
        assert change.is_modified is is_modified

    assert change.event == event
    check_predicates(**predicates)

    assert change.book.equals(
        change.old if event == ChangeEvent.REMOVED else change.new
    ), "the book property gives you the new one, unless it's missing"


#################################################################################


def test_formatted_value() -> None:
    """It can be formatted according to a default or overriden format."""

    value = FormattedValue(1 / 3, "0.3f")
    assert f"{value}" == "0.333", "Use the default format"

    value = FormattedValue(1e6, "0.3f")
    assert f"{value:_.0f}" == "1_000_000", "Override the default format"


#################################################################################


def test_value_formats_extend() -> None:
    """The format strings in a ValueFormats object can be replaced/extended."""

    value_formats = ValueFormats()

    assert value_formats.extend({}), "extend with no modifications"

    value_formats.extend({"Blah": "%Y"})
    assert value_formats.formats["Blah"] == "%Y", "Added a new format"

    assert "Blah" not in ValueFormats().formats, "The class's formats are unchanged"

    value_formats.extend({"float64": "0.3f"})
    assert (
        ValueFormats().formats["float64"] != value_formats.formats["float64"]
    ), "Changed an existing format"


def test_value_formats_find() -> None:
    """Searching for a format string."""

    value_formats = ValueFormats().extend({"AvgRating": ".2f"})

    assert (
        value_formats.find("Work", "float64") == "0.0f"
    ), "Found a format string based on the dtype"

    assert (
        value_formats.find("AvgRating", "float64") == ".2f"
    ), "First term takes precedence over the second"

    assert (
        value_formats.find("Blah") == ""
    ), "Not found: default empty string means format using str()"

    assert (
        value_formats.find("Blah", default=".5") == ".5"
    ), "Not found, using the chosen default instead"


#################################################################################


@pytest.mark.parametrize(
    "fmt, expected",
    [
        (
            "Specific field format: {Added}",
            "Specific field format: Monday 18 April 2016",
        ),
        (
            "Default field format: {Read}",
            "Default field format: 2020-06-13",
        ),
        (
            "Default dtype format: {AvgRating}",
            "Default dtype format: 4",
        ),
        (
            "Overridden dtype format: {AvgRating:06.3f}",
            "Overridden dtype format: 04.080",
        ),
        (
            "Various formatting options are available: {Work:_.0f}",
            "Various formatting options are available: 950_451",
        ),
        (
            "Multiple fields: published is {Published} and binding is {Binding}",
            "Multiple fields: published is 1992 and binding is Paperback",
        ),
        (
            "No fields to replace at all",
            "No fields to replace at all",
        ),
    ],
)
def test_book_formatter(fmt: str, expected: str) -> None:
    """A BookFormatter substitutes fields in the format string."""

    value_formats = ValueFormats().extend({"Added": "%A %d %B %Y"})

    formatter = BookFormatter(c.df.dtypes, value_formats)

    assert formatter.format(fmt, BOOK_READ) == expected


def test_book_formatter_additional_args() -> None:
    """A BookFormatter also accepts kwargs."""

    formatter = BookFormatter(c.df.dtypes, ValueFormats())

    assert (
        formatter.format("I think {Title} is {opinion}", BOOK_READ, opinion="great")
        == "I think The Crow Road is great"
    )


#################################################################################

CHANGE_ADDED = Change(old=None, new=BOOK_UNREAD)
CHANGE_REMOVED = Change(old=BOOK_UNREAD, new=None)
CHANGE_STARTED = Change(old=BOOK_PENDING, new=BOOK_CURRENT)
CHANGE_FINISHED = Change(old=BOOK_CURRENT, new=BOOK_READ)
CHANGE_MODIFIED = Change(old=BOOK_UNREAD, new=BOOK_MODIFIED)


@pytest.mark.parametrize(
    "change, event, expected",
    (
        (
            CHANGE_ADDED,
            ChangeEvent.ADDED,
            "Added The Elephant Vanishes by Haruki Murakami to pending",
        ),
        (
            CHANGE_REMOVED,
            ChangeEvent.REMOVED,
            "Removed The Elephant Vanishes by Haruki Murakami from pending",
        ),
        (
            CHANGE_STARTED,
            ChangeEvent.STARTED,
            "Started The Crow Road by Iain Banks",
        ),
        (
            CHANGE_FINISHED,
            ChangeEvent.FINISHED,
            "Finished The Crow Road by Iain Banks",
        ),
        (
            CHANGE_MODIFIED,
            ChangeEvent.MODIFIED,
            "Haruki Murakami, One Of Our Elephants Is Missing",
        ),
        # FIXME what about unmodified?
    ),
)
def test_formatted_header(change: Change, event: ChangeEvent, expected: str) -> None:
    """Header lines for each type of change."""

    book_formatter = BookFormatter(c.df.dtypes, ValueFormats())
    change_styler = ChangeStyler(book_formatter)

    assert change.event == event
    assert change_styler._header(change) == expected


#################################################################################


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
