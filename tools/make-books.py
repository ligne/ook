#!/usr/bin/python3
#
# Create fake collections for testing purposes.
#
from __future__ import annotations

import argparse
from pathlib import Path

from faker import Faker
import numpy as np
import pandas as pd
import pandera as pa

from reading.storage import Store


seed = 1

rng = np.random.default_rng(seed)

faker = Faker("en")
faker.seed_instance(seed)

GENDERS = ["male", "female", "non-binary"]
STANDARD_SHELVES = ["to-read", "currently-reading", "read"]
SHELVES = [*STANDARD_SHELVES, "pending", "library", "elsewhere"]
CATEGORIES = ["novels", "short-stories", "non-fiction", "graphic"]
BINDINGS = ["Paperback", "Hardback"]
LANGUAGES = ["en", "fr"]

###############################################################################

AUTHOR_BASE_SCHEMA = pa.DataFrameSchema(
    columns={
        "AuthorId": pa.Column(int, pa.Check.gt(0), nullable=False, unique=True),
        "Author": pa.Column(str),
    },
    strict=True,
)


AUTHOR_SCHEMA = AUTHOR_BASE_SCHEMA.add_columns(
    {
        "QID": pa.Column(str, pa.Check.str_matches(r"^Q\d+$")),
        "Nationality": pa.Column(str, nullable=True),
        "Gender": pa.Column(str, nullable=True),
        "Description": pa.Column(str),
    }
).set_index(["AuthorId"])


STATUS_SCHEMA = pa.DataFrameSchema(
    columns={
        "Shelf": pa.Column(str),
        "Added": pa.Column("datetime64[ns]"),
        "Started": pa.Column("datetime64[ns]", nullable=True),
        "Read": pa.Column("datetime64[ns]", nullable=True),
        "Rating": pa.Column(
            float,
            checks=[
                pa.Check.ge(1),
                pa.Check.le(5),
                pa.Check(lambda s: s.round() == s),
            ],
            nullable=True,
        ),
        "Borrowed": pa.Column(bool),
    },
    strict=True,
    checks=[
        pa.Check(
            lambda df: (df.Started.isna() | (df.Started >= df.Added))
            & (df.Read.isna() | (df.Read >= df.Started))
        ),
        pa.Check(lambda df: (df.Shelf == "read") ^ df.Rating.isna()),
        pa.Check(lambda df: (df.Shelf == "read") ^ df.Read.isna()),
        pa.Check(lambda df: df.Shelf.isin(["read", "currently-reading"]) ^ df.Started.isna()),
    ],
)


GOODREADS_SCHEMA = pa.DataFrameSchema(
    columns=STATUS_SCHEMA.columns
    | {
        "BookId": pa.Column(int, unique=True),
        "AuthorId": pa.Column(int),
        "Author": pa.Column(str),
        "Title": pa.Column(str),
        "Work": pa.Column(int),
        "Category": pa.Column(str, nullable=True),
        "Scheduled": pa.Column("datetime64", nullable=True),
        "Series": pa.Column(str, nullable=True),
        "SeriesId": pa.Column(float, nullable=True),
        "Entry": pa.Column(object, nullable=True),
        "Binding": pa.Column(str, nullable=True),
        "Published": pa.Column(float, nullable=True),
        "Language": pa.Column(str, nullable=True),
        "Pages": pa.Column(float, nullable=True),
        "AvgRating": pa.Column(float, checks=pa.Check.in_range(1, 5)),
    },
    strict=True,
).set_index(["BookId"])


###############################################################################


@pa.check_output(AUTHOR_BASE_SCHEMA)
def _generate_authors(size: int) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "AuthorId": rng.choice(np.arange(1_000, 10_000_000), size=size, replace=False),
            "Author": [faker.name() for _ in range(size)],
        }
    )


@pa.check_output(STATUS_SCHEMA)
def _generate_statuses(size: int) -> pd.DataFrame:
    shelf = rng.choice(SHELVES, size)
    dates = np.datetime64("today") - np.sort(rng.integers(3650, size=(3, size)), axis=0)

    statuses = pd.DataFrame({"Shelf": shelf})
    statuses = statuses.assign(
        Added=dates[2],
        Started=np.where(
            statuses.Shelf.isin(["read", "currently-reading"]),
            dates[1],
            np.datetime64("nat"),
        ),
        Read=np.where(statuses.Shelf == "read", dates[0], np.datetime64("nat")),
        Rating=np.where(statuses.Shelf == "read", rng.integers(1, 5, size), np.nan),
        Borrowed=np.where(statuses.Shelf.isin(["elsewhere", "library"]), True, False),
    )
    return statuses


###############################################################################


@pa.check_output(AUTHOR_SCHEMA)
@pa.check_input(AUTHOR_BASE_SCHEMA)
def make_authors_table(authors: pd.DataFrame, size: int) -> pd.DataFrame:
    return (
        authors.sample(n=size, random_state=rng)
        .assign(
            QID=np.char.add("Q", rng.choice(np.arange(1_000, 1_000_000), size=size).astype(str)),
            Gender=rng.choice(GENDERS, size=size),
            Nationality=[faker.country_code().lower() for _ in range(size)],
            Description=[faker.sentence() for _ in range(size)],
        )
        .set_index("AuthorId")
    )


@pa.check_output(GOODREADS_SCHEMA)
@pa.check_input(AUTHOR_BASE_SCHEMA)
def make_goodreads_table(authors: pd.DataFrame, size: int) -> pd.DataFrame:
    return pd.concat(
        [
            pd.DataFrame(
                {
                    "BookId": rng.choice(
                        np.arange(1_000_000, 10_000_000),
                        size=size,
                        replace=False,
                    ),
                    "Title": [faker.sentence()[:-1] for _ in range(size)],
                    "Work": rng.choice(np.arange(1_000, 10_000_000), size=size, replace=False),
                    "Category": rng.choice(CATEGORIES, size=size),
                    "Scheduled": pd.NaT,
                    "Series": pd.NA,
                    "SeriesId": np.nan,
                    "Entry": pd.NA,
                    "Binding": rng.choice(BINDINGS, size=size),
                    "Published": rng.integers(-500, 2020, size=size).astype(float),
                    "Language": rng.choice(LANGUAGES, size=size),
                    "Pages": rng.integers(50, 2_000, size=size).astype(float),
                    "AvgRating": np.round(rng.uniform(1, 5, size=size), 2),
                }
            ),
            _generate_statuses(size),
            authors.sample(n=size, replace=True, random_state=rng, ignore_index=True),
        ],
        axis="columns",
    ).set_index("BookId")


def make_books(size: int) -> Store:
    store = Store()

    author_count = size // 3
    authors_size = round(author_count * 0.9)

    authors = _generate_authors(author_count)

    store.authors = make_authors_table(authors, authors_size)
    store.goodreads = make_goodreads_table(authors, size)

    return store


###############################################################################


def arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("size", type=int, default=10)

    return parser


if __name__ == "__main__":
    args = arg_parser().parse_args()

    if not args.output.is_dir():
        print(f"Output: {args.output} is not a directory.")
        exit(1)

    store = make_books(args.size)
    store.save(args.output)

    exit(0)


# vim: ts=4 : sw=4 : et
