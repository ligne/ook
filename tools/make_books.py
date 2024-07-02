#!/usr/bin/python3
#
# Create fake collections for testing purposes.
#
from __future__ import annotations

import argparse
import datetime as dt

from attrs import define


###############################################################################


@define
class Book:
    """Represent a book."""

    BookId: int
    Author: str
    AuthorId: int
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
    Gender: str | None
    Nationality: str | None


###############################################################################


def make_books(size: int) -> int:
    return 0


###############################################################################


def arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("size", type=int, default=10)

    return parser


if __name__ == "__main__":
    args = arg_parser().parse_args()

    exit(make_books(args.size))


# vim: ts=4 : sw=4 : et
