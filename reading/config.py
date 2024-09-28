# vim: ts=4 : sw=4 : et

"""Configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, TypedDict

import attr
from typing_extensions import Self
import yaml


SHELVES = {"pending", "elsewhere", "library", "ebooks", "kindle", "to-read"}
CATEGORIES = {"novels", "short-stories", "non-fiction", "graphic", "poetry", "articles"}


class ColumnBase(TypedDict):
    """Required columns for a column."""

    name: str
    store: list[str]


class Column(ColumnBase, total=False):
    """Optional fields for a column."""

    merge: str
    type: str


_COLUMNS: list[Column] = [
    {
        "name": "QID",
        "store": ["authors"],
    },
    {
        "name": "BookId",
        "store": ["books"],
        "merge": "first",
    },
    {
        "name": "Author",
        "store": ["goodreads", "ebooks", "books", "authors"],
        "merge": "first",
    },
    {
        "name": "AuthorId",
        "store": ["goodreads", "books"],
        "merge": "first",
    },
    {
        "name": "Title",
        "store": ["goodreads", "ebooks", "books"],
        "merge": "first",
    },
    {
        "name": "Work",
        "store": ["goodreads", "books"],
        "merge": "first",
    },
    {
        "name": "Shelf",
        "store": ["goodreads"],
        "merge": "first",
    },
    {
        "name": "Category",
        "store": ["goodreads", "ebooks", "books"],
        "merge": "first",
    },
    {
        "name": "Scheduled",
        "store": ["goodreads"],
        "type": "date",
        "merge": "first",
    },
    {
        "name": "Borrowed",
        "store": ["goodreads"],
        "merge": "first",
    },
    {
        "name": "Series",
        "store": ["goodreads", "books"],
        "merge": "first",
    },
    {
        "name": "SeriesId",
        "store": ["goodreads", "books"],
        "merge": "first",
    },
    {
        "name": "Entry",
        "store": ["goodreads", "books"],
    },
    {
        "name": "Binding",
        "store": ["goodreads", "scraped"],
        "merge": "first",
    },
    {
        "name": "Published",
        "store": ["goodreads", "books"],
        # Can't convert Published to a date as pandas' range isn't big enough
        "merge": "first",
    },
    {
        "name": "Language",
        "store": ["goodreads", "ebooks"],
        "merge": "first",
    },
    {
        "name": "Pages",
        "store": ["goodreads", "books", "scraped"],
        "merge": "sum",
    },
    {
        "name": "Words",
        "store": ["ebooks"],
        "merge": "sum",
    },
    {
        "name": "Added",
        "store": ["goodreads", "ebooks"],
        "type": "date",
        "merge": "min",
    },
    {
        "name": "Started",
        "store": ["goodreads", "scraped"],
        "type": "date",
        "merge": "min",
    },
    {
        "name": "Read",
        "store": ["goodreads", "scraped"],
        "type": "date",
        "merge": "max",
    },
    {
        "name": "Rating",
        "store": ["goodreads"],
        "merge": "mean",
    },
    {
        "name": "AvgRating",
        "store": ["goodreads"],
        "merge": "first",
    },
    {
        "name": "Gender",
        "store": ["authors"],
        "merge": "first",
    },
    {
        "name": "Nationality",
        "store": ["authors"],
        "merge": "first",
    },
    {
        "name": "Description",
        "store": ["authors"],
    },
    {
        "name": "_Mask",
        "store": [],
        "merge": "any",
    },
]


# columns for various CSVs (eg goodreads, ebooks)
def df_columns(store: str) -> list[str]:
    """Return a list of the columns that should be included in $store."""
    return [col["name"] for col in _COLUMNS if store in col["store"]]


def date_columns(store: str) -> list[str]:
    """Return a list of the columns that should be treated as dates."""
    return [col["name"] for col in _COLUMNS if store in col["store"] and col.get("type") == "date"]


def merge_preferences() -> dict[str, str]:
    """Return a dict specifying how volumes of the same book should be merged."""
    return {"BookId": "first"} | {col["name"]: col["merge"] for col in _COLUMNS if "merge" in col}


################################################################################

_CATEGORIES = {
    "graphic": (
        [
            "graphic-novels",
            "comics",
            "graphic-novel",
        ],
    ),
    "short-stories": (
        [
            "short-story",
            "nouvelles",
            "short-story-collections",
            "relatos-cortos",
        ],
    ),
    "non-fiction": (
        [
            "nonfiction",
            "essays",
        ],
        [
            "education",
            "theology",
            "linguistics",
            "architecture",
            "history",
            "art",
            "very-short-introductions",
        ],
    ),
    "novels": (
        [
            "novel",
            "roman",
            "romans",
        ],
        [
            "fiction",
        ],
    ),
}


def category_patterns() -> tuple[list[list[str]], list[list[str]]]:
    patterns = []
    guesses = []

    for name, pats in _CATEGORIES.items():
        patterns.append([name] + pats[0])
        if len(pats) > 1:
            guesses.append([name] + pats[1])

    return (patterns, guesses)


################################################################################

_DEFAULTS = {
    "kindle.words_per_page": 390,
    "scheduled": [],
}


@attr.s
class Config:
    """Configuration."""

    _conf = attr.ib()

    @classmethod
    def from_file(cls, filename: str | Path = "data/config.yml") -> Self:
        """Create from $filename."""
        try:
            with open(filename) as fh:
                # from yaml import CSafeLoader
                # conf = yaml.load(fh, Loader=CSafeLoader)
                conf = yaml.safe_load(fh)
        except FileNotFoundError:
            conf = {}

        return cls(conf)

    def __call__(self, key: str):
        value = self._conf

        try:
            for segment in key.split("."):
                value = value[segment]
        except KeyError:
            # TODO use defaults and/or emit warning
            return _DEFAULTS.get(key)

        return value

    def reset(self, conf=None) -> None:
        """Set to an empty configuration."""
        self._conf = conf or {}
