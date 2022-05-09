# vim: ts=4 : sw=4 : et

import itertools
from typing import Tuple

import pandas as pd
import pytest

from reading.chain import Chain, Missing, Order, _windows
from reading.collection import Collection


################################################################################


def test_chain():
    """General tests."""
    c = Collection.from_dir("t/data/2019-12-04")

    s = Chain(df=c.all)

    assert s, "Created a Chain"
    assert s.order == Order.Published, "Default is to use published order"
    assert s.missing == Missing.Ignore, "Default is to ignore"

    assert (
        repr(s) == "Chain(_df=[157 books], order=Order.Published, missing=Missing.Ignore)"
    ), "Legible __repr__ for the Chain"


def test_from_series_id():
    c = Collection.from_dir("t/data/2019-12-04")

    s = Chain.from_series_id(c.all, 49118)
    assert s, "Created a Chain from a SeriesId"
    assert s.order == Order.Series, "Series are read in order"
    assert s.missing == Missing.Ignore, "Missing books are ignored by default"


def test_from_series_name():
    c = Collection.from_dir("t/data/2019-12-04")

    s = Chain.from_series_name(c.all, "Culture")
    assert s, "Created a Chain from a series name"
    assert s.order == Order.Series, "Series are read in order"
    assert s.missing == Missing.Ignore, "Missing books are ignored by default"

    # FIXME missing/duplicate series names


def test_from_author_id():
    c = Collection.from_dir("t/data/2019-12-04")

    s = Chain.from_author_id(c.all, 3354)
    assert s, "Created a Chain from an AuthorId"
    assert s.order == Order.Published, "Authors are read in published order by default"
    assert s.missing == Missing.Ignore, "Authors have no missing books to ignore"


def test_from_author_name():
    c = Collection.from_dir("t/data/2019-12-04")

    s = Chain.from_author_name(c.all, "Murakami")
    assert s, "Created a Chain from an author name"
    assert s.order == Order.Published, "Authors are read in published order by default"
    assert s.missing == Missing.Ignore, "Authors have no missing books to ignore"

    # FIXME missing/duplicate author names


def test_chain_options():
    c = Collection.from_dir("t/data/2019-12-04")

    s = Chain.from_series_id(c.all, 49118, order=Order.Published)
    assert s.order == Order.Published, "Can override the order of series"

    # FIXME no alternative Missing values to test


################################################################################


def test_read():
    c = Collection.from_dir("t/data/2019-12-04")

    s = Chain.from_author_name(c.all, "Murakami")
    assert list(s.read.Title) == [
        "Hard-Boiled Wonderland and the End of the World",
        "Norwegian Wood",
    ], "Read Chain"

    s = Chain.from_author_name(c.all, "Leroux")
    assert s.read.empty, "Unread Chain"


################################################################################


def test_currently_reading():
    c = Collection.from_dir("t/data/2019-12-04")

    s = Chain.from_author_name(c.all, "Vonnegut")
    assert s.currently_reading, "currently reading Vonnegut"

    s = Chain.from_author_name(c.all, "Murakami")
    assert not s.currently_reading, "not currently reading Murakami"


################################################################################


def test_last_read():
    c = Collection.from_dir("t/data/2019-12-04")

    s = Chain.from_author_name(c.all, "Gaston Leroux")
    assert s.last_read is None, "Never read"

    s = Chain.from_author_name(c.all, "Vonnegut")
    assert s.last_read.date() == pd.Timestamp("today").date(), "Currently reading"

    s = Chain.from_author_name(c.all, "Murakami")
    assert str(s.last_read.date()) == "2019-08-26", "Previously read"


################################################################################


def test_sort():
    c = Collection.from_dir("t/data/2019-12-04")

    # shuffle them up a bit
    books = c.df[c.df.Series.str.contains("Culture", na=False)].sort_values("Title")

    s = Chain(df=books, order=Order.Published)
    values = list(s.sort()._df.Published)
    assert values == sorted(values), "Sorted by published date"

    s.order = Order.Series
    values = list(s.sort()._df.Entry)
    assert values == sorted(values), "Sorted by entry"

    s.order = Order.Added
    values = list(s.sort()._df.Added)
    assert values == sorted(values), "Sorted by added date"


def test_numeric_sort():
    """Ensure the entries are sorted numerically rather than as alphabetically."""
    c = Collection.from_dir("t/data/2019-12-04")

    s = Chain.from_series_name(c.df, "Rougon-Macquart")
    assert list(s.sort()._df.Entry) == [str(x + 1) for x in range(20)]


################################################################################


def test_remaining():
    c = Collection.from_dir("t/data/2019-12-04")

    # shuffle them up a bit
    books = c.df
    all_shelves = set(books.Shelf)
    assert all_shelves == {
        "currently-reading",
        "ebooks",
        "elsewhere",
        "kindle",
        "library",
        "pending",
        "read",
        "to-read",
    }

    s = Chain(df=books, order=Order.Published)

    remaining = s.remaining
    assert set(remaining.Shelf) == all_shelves - {
        "currently-reading",
        "read",
        "to-read",
    }, "All but the read and unreadable shelves"


################################################################################


@pytest.mark.parametrize(
    "description,inputs,expected",
    (
        (
            "One book per year",
            (2018, 1, 0),
            [
                "2018-01-01 to 2019-01-01",
                "2019-01-01 to 2020-01-01",
                "2020-01-01 to 2021-01-01",
            ],
        ),
        (
            "Several books per year",
            (2018, 4, 0),
            [
                "2018-01-01 to 2018-04-01",
                "2018-04-01 to 2018-07-01",
                "2018-07-01 to 2018-10-01",
            ],
        ),
        (
            "A different number of books per year",
            (2018, 3, 0),
            [
                "2018-01-01 to 2018-05-01",
                "2018-05-01 to 2018-09-01",
                "2018-09-01 to 2019-01-01",
            ],
        ),
        (
            "Offset into the year",
            (2018, 1, 10),
            [
                "2018-10-01 to 2019-10-01",
                "2019-10-01 to 2020-10-01",
                "2020-10-01 to 2021-10-01",
            ],
        ),
        (
            "Several books a year, but offset",
            (2018, 2, 2),
            [
                "2018-02-01 to 2018-08-01",
                "2018-08-01 to 2019-02-01",
                "2019-02-01 to 2019-08-01",
            ],
        ),
    ),
)
def test_windows(
    description: str,
    inputs: Tuple[int, int, int],
    expected: Tuple[Tuple[int, int]],
):
    start, per_year, offset = inputs
    windows = _windows(start, per_year, offset)

    assert [
        f"{win_start:%F} to {win_end:%F}" for win_start, win_end in itertools.islice(windows, 3)
    ] == expected, description


################################################################################

# re-order the fields to make the tests a bit neater
def _format_schedule(df, sched):
    return [
        (
            str(date.date()),
            df.loc[book_id].Title,
        )
        for book_id, date in sched
    ]


# FIXME probably not needed once there's type annotations
def test_scheduling_raw_output():
    c = Collection.from_dir("t/data/2019-12-04")
    df = c.df[c.df.SeriesId == 49118]
    chain = Chain(df=df)

    schedule = chain.schedule()

    assert list(schedule) == [
        (290574, pd.Timestamp("2022-01-01")),
        (129135, pd.Timestamp("2023-01-01")),
        (3091710, pd.Timestamp("2024-01-01")),
        (9543421, pd.Timestamp("2025-01-01")),
    ], "Got a sequence of (book_id, scheduled) pairs"


def test_scheduling():
    c = Collection.from_dir("t/data/2019-12-04")
    df = c.df[c.df.SeriesId == 49118]
    chain = Chain(df=df)

    schedule = chain.schedule()

    assert _format_schedule(df, schedule) == [
        ("2022-01-01", "Inversions"),
        ("2023-01-01", "Look to Windward"),
        ("2024-01-01", "Matter"),
        ("2025-01-01", "Surface Detail"),
    ], "A basic schedule"
