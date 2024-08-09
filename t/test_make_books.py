# vim: ts=4 : sw=4 : et

from __future__ import annotations

import importlib


mb = importlib.import_module("tools.make-books")


def test__generate_authors() -> None:
    authors = mb._generate_authors(3)

    assert len(authors) == 3
    mb.AUTHOR_BASE_SCHEMA.validate(authors, lazy=True)


def test_make_authors_table() -> None:
    author_ids = mb._generate_authors(10)
    authors = mb.make_authors_table(author_ids, size=3)

    assert len(authors) == 3
    mb.AUTHOR_SCHEMA.validate(authors, lazy=True)


def test__generate_statuses() -> None:
    statuses = mb._generate_statuses(3)

    assert len(statuses) == 3
    mb.STATUS_SCHEMA.validate(statuses, lazy=True)
