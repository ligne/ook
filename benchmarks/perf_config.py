# vim: ts=4 : sw=4 : et

"""Benchmark configuration file operations."""

from __future__ import annotations

from pathlib import Path

from reading.config import Config


################################################################################


def perf_config_load(benchmark, collection_path: Path) -> None:
    """Time required to load the configuration file."""
    config = benchmark(Config.from_file, collection_path / "config.yml")
    assert config("kindle.words_per_page") == 390
