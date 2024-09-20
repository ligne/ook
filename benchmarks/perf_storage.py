# vim: ts=4 : sw=4 : et

"""Benchmark storage operations."""

from __future__ import annotations

from reading.storage import Store


################################################################################


def perf_storage_table_load(benchmark, collection_store: Store) -> None:
    """Time required to load a table from disk."""
    benchmark(getattr, collection_store, "goodreads")
