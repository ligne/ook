# vim: ts=4 : sw=4 : et

import pandas as pd

from reading.chain import Chain, Missing, Order
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
    values = list(s.sort()._df.Series)
    assert values == sorted(values), "Sorted by entry"

    s.order = Order.Added
    values = list(s.sort()._df.Added)
    assert values == sorted(values), "Sorted by added date"


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
