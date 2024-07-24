#!/usr/bin/python3
#
# Create fake collections for testing purposes.
#
from __future__ import annotations

import argparse
import datetime as dt
import random
from typing import Literal, Sequence

import attrs
from attrs import define
from faker import Faker
import numpy as np
import pandas as pd


CORE_SHELVES = ["to-read", "currently-reading", "read"]

SHELVES = [*CORE_SHELVES, "pending", "elsewhere", "library"]
GENDERS = ["male", "female", "non-binary"]
CATEGORIES = ["novels", "short-stories", "non-fiction", "graphic"]
BINDINGS = ["Paperback", "Hardback"]
LANGUAGES = ["en", "fr"]


###############################################################################


@define
class Author:
    """Represent an author."""

    Author: str
    AuthorId: int
    Gender: str | None
    Nationality: str | None


@define
class UnreadBook:
    Shelf: Literal["to-read"] | str
    Added: dt.date
    Started: None
    Read: None
    Rating: None


@define
class CurrentBook:
    Shelf: Literal["currently-reading"]
    Added: dt.date
    Started: dt.date
    Read: None
    Rating: None


@define
class FinishedBook:
    Shelf: Literal["read"]
    Added: dt.date
    Started: dt.date
    Read: dt.date
    Rating: int | None


BookStatus = UnreadBook | CurrentBook | FinishedBook


@define
class SeriesEntry:
    Series: str
    SeriesId: int
    Entry: str | int


@define
class _NoSeries:
    Series: None = None
    SeriesId: None = None
    Entry: None = None


NoSeries = _NoSeries()


@define
class SeriesSpec:
    Series: str
    SeriesId: int
    size: int

    def entries(self) -> list[SeriesEntry]:
        return [SeriesEntry(self.Series, self.SeriesId, entry + 1) for entry in range(self.size)]


@define
class Book:
    """Represent a book."""

    BookId: int
    Title: str
    Work: int
    Category: str | None
    Scheduled: dt.date | None
    Borrowed: bool
    Binding: str | None
    Published: int | None
    Language: str | None
    Pages: int | None
    Words: int | None
    AvgRating: float

    _author: Author
    _status: BookStatus
    _series: SeriesEntry | _NoSeries

    def to_dict(self) -> dict:  # type: ignore[type-arg]
        ret = []
        for k, v in attrs.asdict(self).items():
            if k.startswith("_"):
                ret.extend(v.items())
            else:
                ret.append((k, v))
        return dict(ret)


###############################################################################


def _make_authors(faker: Faker, size: int) -> Sequence[Author]:
    return [
        Author(
            Author=faker.name(),
            AuthorId=faker.random_int(1_000, 10_000_000),
            Gender=faker.optional.random_element(GENDERS),
            Nationality=faker.optional.random_element(
                [
                    faker.country(),
                    faker.country_code().lower(),
                ]
            ),
        )
        for _ in range(size)
    ]


def _make_status(faker: Faker) -> BookStatus:
    shelf = np.random.choice(SHELVES)
    added = faker.date_between("-10y", "today")

    if shelf == "read":
        started, read = sorted(
            [
                faker.date_between(added, "today"),
                faker.date_between(added, "today"),
            ]
        )
        return FinishedBook(
            shelf,
            Added=added,
            Started=started,
            Read=read,
            Rating=faker.optional.random_int(1, 5),
        )
    if shelf == "currently-reading":
        return CurrentBook(
            shelf,
            Added=added,
            Started=faker.date_between(added, "today"),
            Read=None,
            Rating=None,
        )
    return UnreadBook(shelf, Added=added, Started=None, Read=None, Rating=None)


def _make_book(
    faker: Faker,
    author: Author,
    status: BookStatus,
    series: SeriesEntry | _NoSeries = NoSeries,
) -> Book:
    return Book(
        author=author,
        status=status,
        series=series,
        BookId=faker.random_int(1_000, 1_000_000_000),
        Title=faker.sentence()[:-1],
        Work=faker.random_int(1_000, 10_000_000),
        Category=faker.optional.random_element(CATEGORIES, prob=0.1),
        Scheduled=None,
        Borrowed=False,
        Binding=faker.random_element(BINDINGS),
        Published=faker.optional.year(),
        Language=faker.optional.random_element(LANGUAGES, prob=0.1),
        Pages=faker.random_int(1, 1500),
        Words=None,
        AvgRating=np.random.uniform(1, 5)
    )


###############################################################################


def make_series(faker: Faker, author: Author, size: int) -> list[Book]:
    series = SeriesSpec(
        Series=faker.sentence(4)[:-1],
        SeriesId=random.randint(1_000, 1_000_000),
        size=random.randint(1, size),
    )

    # for each entry, create a random book
    # FIXME or skip it
    return [_make_book(faker, author, _make_status(faker), entry) for entry in series.entries()]


def make_books(faker: Faker, size: int) -> int:
    author_count = max(1, size // 3)

    books: list[Book] = []
    remaining = size

    authors = _make_authors(faker, author_count)

    # create some series. approximately 25%
    while remaining > int(size * 0.75):
        series = make_series(faker, random.choice(authors), size=random.randint(1, 10))
        books.extend(series)
        remaining -= len(series)

    books.extend(
        [
            _make_book(faker, faker.random_element(authors), _make_status(faker))
            for _ in range(remaining)
        ]
    )

    pd.set_option("display.max_rows", None)
    pd.set_option("display.width", None)
    print(pd.DataFrame.from_dict([book.to_dict() for book in books]))

    return 0


###############################################################################


def arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("size", type=int, default=10)

    return parser


if __name__ == "__main__":
    args = arg_parser().parse_args()

    faker = Faker()

    exit(make_books(faker, args.size))


# vim: ts=4 : sw=4 : et
