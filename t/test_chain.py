# vim: ts=4 : sw=4 : et

from __future__ import annotations

import datetime as dt
import itertools
from typing import Tuple

import pandas as pd
import pytest

from reading.chain import Chain, Missing, Order, _dates, _windows
from reading.collection import Collection


################################################################################


def test_chain() -> None:
    """General tests."""
    c = Collection.from_dir("t/data/2019-12-04")

    s = Chain(df=c.all)

    assert s, "Created a Chain"
    assert s.order == Order.PUBLISHED, "Default is to use published order"
    assert s.missing == Missing.IGNORE, "Default is to ignore"

    assert (
        repr(s) == "Chain(_df=[157 books], order=Order.PUBLISHED, missing=Missing.IGNORE)"
    ), "Legible __repr__ for the Chain"


def test_from_series_id() -> None:
    c = Collection.from_dir("t/data/2019-12-04")

    s = Chain.from_series_id(c.all, 49118)
    assert s, "Created a Chain from a SeriesId"
    assert s.order == Order.SERIES, "Series are read in order"
    assert s.missing == Missing.IGNORE, "Missing books are ignored by default"


def test_from_series_name() -> None:
    c = Collection.from_dir("t/data/2019-12-04")

    s = Chain.from_series_name(c.all, "Culture")
    assert s, "Created a Chain from a series name"
    assert s.order == Order.SERIES, "Series are read in order"
    assert s.missing == Missing.IGNORE, "Missing books are ignored by default"

    # FIXME missing/duplicate series names


def test_from_author_id() -> None:
    c = Collection.from_dir("t/data/2019-12-04")

    s = Chain.from_author_id(c.all, 3354)
    assert s, "Created a Chain from an AuthorId"
    assert s.order == Order.PUBLISHED, "Authors are read in published order by default"
    assert s.missing == Missing.IGNORE, "Authors have no missing books to ignore"


def test_from_author_name() -> None:
    c = Collection.from_dir("t/data/2019-12-04")

    s = Chain.from_author_name(c.all, "Murakami")
    assert s, "Created a Chain from an author name"
    assert s.order == Order.PUBLISHED, "Authors are read in published order by default"
    assert s.missing == Missing.IGNORE, "Authors have no missing books to ignore"

    # FIXME missing/duplicate author names


def test_chain_options() -> None:
    c = Collection.from_dir("t/data/2019-12-04")

    s = Chain.from_series_id(c.all, 49118, order=Order.PUBLISHED)
    assert s.order == Order.PUBLISHED, "Can override the order of series"

    # FIXME no alternative Missing values to test


################################################################################


def test_read() -> None:
    c = Collection.from_dir("t/data/2019-12-04")

    s = Chain.from_author_name(c.all, "Murakami")
    assert list(s.read.Title) == [
        "Hard-Boiled Wonderland and the End of the World",
        "Norwegian Wood",
    ], "Read Chain"

    s = Chain.from_author_name(c.all, "Leroux")
    assert s.read.empty, "Unread Chain"


################################################################################


def test_currently_reading() -> None:
    c = Collection.from_dir("t/data/2019-12-04")

    s = Chain.from_author_name(c.all, "Vonnegut")
    assert s.currently_reading, "currently reading Vonnegut"

    s = Chain.from_author_name(c.all, "Murakami")
    assert not s.currently_reading, "not currently reading Murakami"


################################################################################


def test_last_read() -> None:
    c = Collection.from_dir("t/data/2019-12-04")

    s = Chain.from_author_name(c.all, "Gaston Leroux")
    assert s.last_read is None, "Never read"

    s = Chain.from_author_name(c.all, "Vonnegut")
    assert s.last_read.date() == pd.Timestamp("today").date(), "Currently reading"

    s = Chain.from_author_name(c.all, "Murakami")
    assert str(s.last_read.date()) == "2019-08-26", "Previously read"


################################################################################


def test_sort() -> None:
    c = Collection.from_dir("t/data/2019-12-04")

    # shuffle them up a bit
    books = c.df[c.df.Series.str.contains("Culture", na=False)].sort_values("Title")

    s = Chain(df=books, order=Order.PUBLISHED)
    values = list(s.sort()._df.Published)
    assert values == sorted(values), "Sorted by published date"

    s.order = Order.SERIES
    values = list(s.sort()._df.Entry)
    assert values == sorted(values), "Sorted by entry"

    s.order = Order.ADDED
    values = list(s.sort()._df.Added)
    assert values == sorted(values), "Sorted by added date"


def test_numeric_sort() -> None:
    """Ensure the entries are sorted numerically rather than as alphabetically."""
    c = Collection.from_dir("t/data/2019-12-04")

    s = Chain.from_series_name(c.df, "Rougon-Macquart")
    assert list(s.sort()._df.Entry) == [str(x + 1) for x in range(20)]


################################################################################


def test_remaining() -> None:
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

    s = Chain(df=books, order=Order.PUBLISHED)

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
    expected: list[str],
) -> None:
    start, per_year, offset = inputs
    windows = _windows(start, per_year, offset)

    assert [
        f"{win_start:%F} to {win_end:%F}" for win_start, win_end in itertools.islice(windows, 3)
    ] == expected, description


################################################################################


@pytest.mark.parametrize(
    "description,today,inputs,expected",
    (
        (
            "Start of the year, default settings",
            "2020-02-04",
            {},
            [
                "2020-01-01",
                "2021-01-01",
                "2022-01-01",
            ],
        ),
        (
            "Start of the year, several per year",
            "2020-02-04",
            {"per_year": 4},
            [
                "2020-01-01",
                "2020-04-01",
                "2020-07-01",
            ],
        ),
        # start date
        (
            "Start of the year, start in a future year",
            "2020-02-04",
            {"start": 2022},
            [
                "2022-01-01",
                "2023-01-01",
                "2024-01-01",
            ],
        ),
        (
            "Start of the year, start this year",
            "2020-02-04",
            {"start": 2020},
            [
                "2020-01-01",
                "2021-01-01",
                "2022-01-01",
            ],
        ),
        (
            "Start of the year, start in a past year",
            "2020-02-04",
            {"start": 2019},
            [
                "2020-01-01",
                "2021-01-01",
                "2022-01-01",
            ],
        ),
        # previously-read
        (
            "Start of the year, read this year",
            "2020-02-04",
            {"last_read": "2020-01-04"},
            [
                "2021-01-01",
                "2022-01-01",
                "2023-01-01",
            ],
        ),
        (
            "Start of the year, read this year, but force",
            "2020-02-04",
            {"last_read": "2020-01-04", "force": True},
            [
                "2020-07-04",  # first is delayed
                "2021-01-01",
                "2022-01-01",
            ],
        ),
        (
            "Start of the year, read late last year",
            "2020-02-04",
            {"last_read": "2019-12-04"},
            [
                "2020-06-04",  # first is delayed
                "2021-01-01",
                "2022-01-01",
            ],
        ),
        (
            "Dates are only adjusted when per_year=1",
            "2020-02-04",
            {"per_year": 4, "last_read": "2019-12-04"},
            [
                "2020-01-01",
                "2020-04-01",
                "2020-07-01",
            ],
        ),
        # starting later in the year
        (
            "Later in the year, skipped a window",
            "2020-05-04",
            {
                "per_year": 4,
            },
            [
                "2020-04-01",
                "2020-07-01",
                "2020-10-01",
            ],
        ),
        # starting near the end of the year
        (
            "End of the year, default settings",
            "2019-12-04",
            {},
            [
                "2019-01-01",
                "2020-01-01",
                "2021-01-01",
            ],
        ),
        (
            "End of the year, several per year",
            "2019-12-04",
            {"per_year": 4},
            [
                "2019-10-01",
                "2020-01-01",
                "2020-04-01",
            ],
        ),
        (
            "End of the year, read this year",
            "2019-12-04",
            {"last_read": "2019-04-04"},
            [
                "2020-01-01",
                "2021-01-01",
                "2022-01-01",
            ],
        ),
        (
            "End of the year, read late this year: next year is postponed",
            "2019-12-04",
            {"last_read": "2019-08-26"},
            [
                "2020-02-26",
                "2021-01-01",
                "2022-01-01",
            ],
        ),
        (
            "End of the year, read late this year: next year is postponed",
            "2019-12-04",
            {"per_year": 4},
            [
                "2019-10-01",
                "2020-01-01",
                "2020-04-01",
            ],
        ),
    ),
)
def test_dates(description, today, inputs, expected) -> None:
    today = pd.Timestamp(today)

    start = inputs.get("start", today.year)
    per_year = inputs.get("per_year", 1)
    offset = inputs.get("offset", 0)
    last_read = inputs.get("last_read", None)
    force = inputs.get("force", False)

    if last_read:
        last_read = pd.Timestamp(last_read)

    dates = _dates(
        _windows(start, per_year, offset),
        per_year=per_year,
        last_read=last_read,
        force=force,
        date=today,
    )

    assert [f"{date:%F}" for date in itertools.islice(dates, 3)] == expected, description


################################################################################


# re-order the fields to make the tests a bit neater
def _format_schedule(
    df: pd.DataFrame,
    sched: list[tuple[int, dt.datetime]],
) -> list[tuple[str, str]]:
    return [
        (
            str(date.date()),
            df.loc[book_id].Title,
        )
        for book_id, date in sched
    ]


# FIXME probably not needed once there's type annotations
def test_scheduling_raw_output() -> None:
    c = Collection.from_dir("t/data/2019-12-04")
    df = c.df[c.df.SeriesId == 49118]
    chain = Chain(df=df)

    schedule = chain.schedule()

    assert list(schedule) == [
        (290574, pd.Timestamp("2024-01-01")),
        (129135, pd.Timestamp("2025-01-01")),
        (3091710, pd.Timestamp("2026-01-01")),
        (9543421, pd.Timestamp("2027-01-01")),
    ], "Got a sequence of (book_id, scheduled) pairs"


def test_scheduling() -> None:
    c = Collection.from_dir("t/data/2019-12-04")
    df = c.df[c.df.SeriesId == 49118]
    chain = Chain(df=df)

    schedule = chain.schedule()

    assert _format_schedule(df, schedule) == [
        ("2024-01-01", "Inversions"),
        ("2025-01-01", "Look to Windward"),
        ("2026-01-01", "Matter"),
        ("2027-01-01", "Surface Detail"),
    ], "A basic schedule"

    # FIXME add more tests from 8580c313a468ebdd073d256cbf90884613882956 if it seems useful
