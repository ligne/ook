# vim: ts=4 : sw=4 : et

"""End-to-end performance tests."""

from __future__ import annotations

from pathlib import Path
import subprocess

import pytest


################################################################################


@pytest.mark.parametrize(
    "args",
    (
        [],
        ["--language=fr"],
        ["--categories=short-stories"],
        ["--new-nationalities"],
        ["--new-authors", "--old-nationalities"],
        ["--all"],
    ),
    ids=" ".join,
)
@pytest.mark.parametrize("command", ("scheduled", "suggest"))
def perf_ook_command(benchmark, collection_path: Path, command: str, args: list[str]) -> None:
    """Time required to run the full command."""
    run = benchmark(
        subprocess.run,
        ("ook", f"--data-dir={collection_path}", command, *args),
        env={"PATH": "."},
    )
    run.check_returncode()
