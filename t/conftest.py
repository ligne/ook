# vim: ts=4 : sw=4 : et

"""Fixtures and helpers for testing."""

import pytest

from reading.collection import Collection


@pytest.fixture()
def collection():
    """Return a collection factory."""
    def _get_collection(name, fixes=False, **kwargs):
        return Collection(
            gr_csv=f"t/data/goodreads-{name}.csv",
            ebook_csv=f"t/data/ebooks-{name}.csv",
            fixes=fixes,
            **kwargs,
        )

    return _get_collection
