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


@pytest.fixture(autouse=True)
def _generate_metadata(collection_path: Path) -> None:
    """Ensure the metadata files have been generated before starting."""
    from reading.collection import rebuild_metadata

    if not (collection_path / "metadata-ebooks.csv").exists():
        rebuild_metadata(Store(collection_path), Config.from_file(collection_path / "config.yml"))


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
