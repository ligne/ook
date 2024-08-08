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


###############################################################################


@pa.check_output(AUTHOR_BASE_SCHEMA)
def _generate_authors(size: int):
    return pd.DataFrame(
        {
            "AuthorId": rng.choice(np.arange(1_000, 10_000_000), size=size),
            "Author": [faker.name() for _ in range(size)],
        }
    )


###############################################################################


@pa.check_output(AUTHOR_SCHEMA)
@pa.check_input(AUTHOR_BASE_SCHEMA)
def make_authors_table(authors, size: int):
    return (
        authors.sample(n=size)
        .assign(
            QID=np.char.add("Q", rng.choice(np.arange(1_000, 1_000_000), size=size).astype(str)),
            Gender=rng.choice(GENDERS, size=size),
            Nationality=[faker.country_code().lower() for _ in range(size)],
            Description=[faker.sentence() for _ in range(size)],
        )
        .set_index("AuthorId")
    )


def make_books(size: int) -> Store:
    store = Store()

    author_count = size // 3
    authors_size = round(author_count * 0.9)

    authors = _generate_authors(author_count)

    store.authors = make_authors_table(authors, authors_size)

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
