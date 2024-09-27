# vim: ts=4 : sw=4 : et

"""Fixtures and helpers for benchmarking."""

from __future__ import annotations

from pathlib import Path

import pytest

from reading.collection import Collection
from reading.config import Config
from reading.storage import Store


################################################################################


@pytest.fixture(params=["small", "medium", "large"])
def collection_path(request: pytest.FixtureRequest) -> Path:
    """Return the path to each of the benchmark collections."""
    return Path("benchmarks/data/collections", request.param)


@pytest.fixture()
def collection_store(collection_path: Path) -> Store:
    """Return each of the benchmark collections as a Store."""
    return Store(collection_path)


@pytest.fixture()
def collection(collection_path: Path) -> Collection:
    """Return each of the benchmark collections in Collection form."""
    return Collection.from_store(
        Store(collection_path),
        Config.from_file(collection_path / "config.yml"),
    )
