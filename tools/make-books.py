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
import yaml

from reading.config import Config
from reading.storage import Store


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
    unique_column_names=True,
)

AUTHOR_SCHEMA = AUTHOR_BASE_SCHEMA.add_columns(
    {
        "QID": pa.Column(str, pa.Check.str_matches(r"^Q\d+$")),
        "Nationality": pa.Column(str, nullable=True),
        "Gender": pa.Column(str, nullable=True),
        "Description": pa.Column(str),
    },
).set_index(["AuthorId"])

AUTHOR_FIX_SCHEMA = pa.DataFrameSchema(
    {
        "Author": pa.Column(str, nullable=True),
        "AuthorId": pa.Column(int),
        "Gender": pa.Column(str, nullable=True),
        "Nationality": pa.Column(str, nullable=True),
    },
    strict=True,
    unique_column_names=True,
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
    unique_column_names=True,
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

EBOOK_SCHEMA = pa.DataFrameSchema(
    {
        "BookId": pa.Column(str, unique=True),
        "Author": pa.Column(str),
        "Title": pa.Column(str),
        "Category": pa.Column(str),
        "Language": pa.Column(str),
        "Words": pa.Column(int),
        "Added": pa.Column("datetime64"),
    },
    strict=True,
    unique_column_names=True,
).set_index(["BookId"])

BOOK_SCHEMA = pa.DataFrameSchema(
    {
        "KindleId": pa.Column(str, unique=True),
        "BookId": pa.Column(int, unique=True),
        "Author": pa.Column(str),
        "AuthorId": pa.Column(int),
        "Title": pa.Column(str),
        "Work": pa.Column(int),
        "Category": pa.Column(str, nullable=True),
        "Series": pa.Column(str, nullable=True),
        "SeriesId": pa.Column(float, nullable=True),
        "Entry": pa.Column(object, nullable=True),
        "Published": pa.Column(float, nullable=True),
        "Language": pa.Column(str, nullable=True),
        "Pages": pa.Column(float, nullable=True),
    },
    strict=True,
    unique_column_names=True,
).set_index(["KindleId"])

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
    unique_column_names=True,
).set_index(["BookId"])

SCRAPED_SCHEMA = pa.DataFrameSchema(
    {
        "BookId": pa.Column(int, unique=True),
        "Binding": pa.Column(str, nullable=True),
        "Pages": pa.Column(float, nullable=True),
    },
    #    strict=True,
    unique_column_names=True,
).set_index(["BookId"])

BOOK_FIX_SCHEMA = pa.DataFrameSchema(
    {
        "BookId": pa.Column(int),
        "Language": pa.Column(str, nullable=True),
        "Title": pa.Column(str, nullable=True),
        "Published": pa.Column(float, nullable=True),
        "Category": pa.Column(str, nullable=True),
        "Pages": pa.Column(float, nullable=True),
    },
    strict=True,
    unique_column_names=True,
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
                    "AvgRating": rng.integers(100, 501, size=size) / 100,
                }
            ),
            _generate_statuses(size),
            authors.sample(n=size, replace=True, random_state=rng, ignore_index=True),
        ],
        axis="columns",
    ).set_index("BookId")


@pa.check_output(EBOOK_SCHEMA)
def make_ebooks_table(size: int) -> pd.DataFrame:
    return (
        pd.DataFrame(
            {
                "Author": [faker.name() for _ in range(size)],
                "Title": [faker.sentence()[:-1] for _ in range(size)],
                "Category": rng.choice(CATEGORIES, size=size),
                "Language": rng.choice(LANGUAGES, size=size),
                "Words": rng.integers(1000, 1_000_000, size=size),
                "Added": np.datetime64("today") - rng.integers(3650, size=size),
            }
        )
        .assign(
            BookId=lambda df: df.Category.str.cat(
                [
                    faker.word() + rng.integers(10_000_000).astype(str) + ".mobi"
                    for _ in range(size)
                ],
                sep="/",
            )
        )
        .set_index("BookId")
    )


@pa.check_output(BOOK_SCHEMA)
@pa.check_input(EBOOK_SCHEMA)
def make_books_table(ebooks, authors, size: int) -> pd.DataFrame:
    return pd.concat(
        [
            ebooks.assign(Pages=ebooks.Words / 300)
            .drop(columns=["Words", "Added", "Author"])
            .sample(n=size, random_state=rng)
            .reset_index()
            .rename(columns={"BookId": "KindleId"})
            .assign(
                BookId=rng.choice(np.arange(1_000, 1_000_000), size=size, replace=False),
                Work=rng.choice(np.arange(1_000, 10_000_000), size=size, replace=False),
                Published=rng.integers(-500, 2020, size=size).astype(float),
                Series=pd.NA,
                SeriesId=np.nan,
                Entry=pd.NA,
            ),
            authors.sample(n=size, replace=True, random_state=rng, ignore_index=True),
        ],
        axis="columns",
    ).set_index("KindleId")


@pa.check_output(SCRAPED_SCHEMA)
@pa.check_input(GOODREADS_SCHEMA)
def make_scraped_table(goodreads) -> pd.DataFrame:
    size = len(goodreads)
    return pd.DataFrame(
        {
            "Binding": np.where(
                rng.random(size=size) > 0.06, rng.choice(BINDINGS, size=size), None
            ),
            "Pages": np.where(
                rng.random(size=size) > 0.5,
                rng.integers(50, 2_000, size=size).astype(float),
                np.nan,
            ),
            "Started": None,
            "Read": None,
        },
        index=goodreads.index,
    ).dropna(how="all")


@pa.check_output(BOOK_FIX_SCHEMA)
@pa.check_input(GOODREADS_SCHEMA)
def make_book_fixes(goodreads, size):
    fixed_books = goodreads.sample(frac=0.4, random_state=rng)
    return pd.concat(
        [
            fixed_books[column].sample(frac=fraction, random_state=rng)
            for column, fraction in {
                "Language": 0.75,
                "Title": 0.04,
                "Published": 0.2,
                "Category": 0.1,
                "Pages": 0.04,
            }.items()
        ],
        axis="columns",
    ).sort_index()


@pa.check_output(AUTHOR_FIX_SCHEMA)
@pa.check_input(AUTHOR_SCHEMA)
def make_author_fixes(authors, author_ids, size):
    fixed_authors = authors.sample(frac=0.03, random_state=rng)
    return pd.DataFrame(
        {
            column: fixed_authors[column].sample(frac=fraction, random_state=rng)
            for column, fraction in {
                "Gender": 0.75,
                "Nationality": 0.85,
                "Author": 0.01,
            }.items()
        },
    ).sort_index()


def _tidy_for_yaml(df) -> list[dict]:
    return [
        {
            k: (int(v) if k in ("Published", "Pages") else v)
            for k, v in record.items()
            if not pd.isna(v)
        }
        for record in df.reset_index().to_dict(orient="records")
    ]


def make_config(author_ids, size: int, store: Store):
    return {
        "fixes": _tidy_for_yaml(make_book_fixes(store.goodreads, size)),
        "authors": _tidy_for_yaml(make_author_fixes(store.authors, author_ids, size)),
    }


def make_books(size: int) -> Store:
    store = Store()

    author_count = round(size * 0.66)
    authors_size = round(author_count * 0.9)

    authors = _generate_authors(author_count)

    ebooks_size = size // 7
    goodreads_size = size - ebooks_size
    books_size = round(ebooks_size * 0.9)

    store.authors = make_authors_table(authors, authors_size)
    store.goodreads = make_goodreads_table(authors, goodreads_size)
    store.scraped = make_scraped_table(store.goodreads)
    store.ebooks = make_ebooks_table(ebooks_size)
    store.books = make_books_table(store.ebooks, authors, books_size)

    config = make_config(authors, size, store)

    return store, config


###############################################################################


def arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--size", type=int, default=100)

    return parser


if __name__ == "__main__":
    args = arg_parser().parse_args()

    if not args.output.is_dir():
        print(f"Output: {args.output} is not a directory.")
        exit(1)

    faker = Faker("en")
    faker.seed_instance(args.seed)
    rng = np.random.Generator(np.random.PCG64DXSM(args.seed))

    store, config = make_books(args.size)
    store.save(args.output)
    (args.output / "config.yml").write_text(yaml.dump(config))

    exit(0)


# vim: ts=4 : sw=4 : et
