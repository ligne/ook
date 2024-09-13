# vim: ts=4 : sw=4 : et

"""Benchmark Collection operations."""

from __future__ import annotations

from pathlib import Path

import pytest

from reading.collection import Collection


################################################################################


@pytest.mark.parametrize("fixes", (True, False), ids=lambda x: f"fixes={x}")
@pytest.mark.parametrize("metadata", (True, False), ids=lambda x: f"metadata={x}")
def perf_collection_creation(benchmark, collection_path: Path, metadata: bool, fixes: bool) -> None:
    """Time required to create a collection."""
    benchmark(
        Collection.from_dir,
        collection_path,
        metadata=metadata,
        fixes=fixes,
    )


@pytest.mark.parametrize("accessor", ("all", "df"), ids=lambda x: f"c.{x}")
@pytest.mark.parametrize("dedup", (True, False), ids=lambda x: f"dedup={x}")
@pytest.mark.parametrize("merge", (True, False), ids=lambda x: f"merge={x}")
def perf_collection_access(
    benchmark,
    collection: Collection,
    merge: bool,
    dedup: bool,
    accessor: str,
) -> None:
    """Time required to get the books out again."""
    if dedup and not merge:
        pytest.xfail("dedup currently requires merge")

    collection.merge = merge
    collection.dedup = dedup

    # FIXME check it returned a sensible result?
    benchmark(getattr, collection, accessor)
