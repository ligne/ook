#!/usr/bin/python3
#
# Create fake collections for testing purposes.
#
from __future__ import annotations

import argparse

from faker import Faker
import numpy as np
import pandas as pd

from reading.storage import Store


seed = 1

rng = np.random.default_rng(seed)

faker = Faker("en")
faker.seed_instance(seed)

GENDERS = ["male", "female", "non-binary"]

###############################################################################


def _generate_authors(size: int):
    return pd.DataFrame(
        {
            "AuthorId": rng.choice(np.arange(1_000, 10_000_000), size=size),
            "Author": [faker.name() for _ in range(size)],
        }
    )


###############################################################################


def make_authors_table(authors, size: int):
    return authors.sample(n=size).assign(
        QID=np.char.add("Q", rng.choice(np.arange(1_000, 1_000_000), size=size).astype(str)),
        Gender=rng.choice(GENDERS, size=size),
        Nationality=[faker.country_code().lower() for _ in range(size)],
        Description=[faker.sentence() for _ in range(size)],
    )


def make_books(size: int) -> int:
    store = Store()

    author_count = size // 3
    authors_size = round(author_count * 0.9)

    authors = _generate_authors(author_count)

    store.authors = make_authors_table(authors, authors_size)

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
