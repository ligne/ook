# vim: ts=4 : sw=4 : et

from __future__ import annotations

import importlib


mb = importlib.import_module("tools.make-books")


def test__generate_authors() -> None:
    authors = mb._generate_authors(3)

    assert len(authors) == 3
    assert list(authors.columns) == ["AuthorId", "Author"]
