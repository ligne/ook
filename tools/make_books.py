#!/usr/bin/python3
#
# Create fake collections for testing purposes.
#
from __future__ import annotations

import argparse
import datetime as dt
from typing import Sequence

import attrs
from attrs import define
from faker import Faker
import pandas as pd


CORE_SHELVES = ["to-read", "currently-reading", "read"]

SHELVES = CORE_SHELVES + ["pending", "elsewhere", "library"]
GENDERS = ["male", "female", "non-binary"]
CATEGORIES = ["novels", "short-stories", "non-fiction", "graphic"]
BINDINGS = ["Paperback", "Hardback"]


###############################################################################


@define
class Author:
    """Represent an author."""

    Author: str
    AuthorId: int
    Gender: str | None
    Nationality: str | None


@define
class Book:
    """Represent a book."""

    BookId: int
    Title: str
    Work: int
    Shelf: str
    Category: str | None
    Scheduled: dt.date | None
    Borrowed: bool
    Series: str | None
    SeriesId: str | None
    Entry: str | int | None
    Binding: str | None
    Published: int | None
    Language: str | None
    Pages: int | None
    Added: dt.date
    Started: dt.date | None
    Read: dt.date | None
    Rating: int | None
    Words: int | None

    _author: Author

    def to_dict(self) -> dict:
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


def _make_book(faker: Faker, author: Author) -> Book:
    return Book(
        author=author,
        BookId=faker.random_int(1_000, 1_000_000_000),
        Title=faker.sentence()[:-1],
        Work=faker.random_int(1_000, 10_000_000),
        Shelf=faker.random_element(SHELVES),
        Category=faker.optional.random_element(CATEGORIES),
        Scheduled=None,
        Borrowed=False,
        Series=None,
        SeriesId=None,
        Entry=None,
        Binding=faker.random_element(BINDINGS),
        Published=faker.optional.year(),
        Language=faker.optional.language_code(),
        Pages=faker.random_int(1, 1500),
        Added=faker.date_between("-10y", "today"),
        Started=None,
        Read=None,
        Rating=None,
        Words=None,
    )


def make_books(faker: Faker, size: int) -> int:
    author_count = max(1, size // 3)

    authors = _make_authors(faker, author_count)
    books = [_make_book(faker, faker.random_element(authors)) for _ in range(size)]

    print([book.to_dict() for book in books])

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
