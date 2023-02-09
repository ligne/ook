# vim: ts=4 : sw=4 : et

"""Fixtures and helpers for testing."""

import pytest

from reading.collection import Collection


@pytest.fixture()
def collection():
    """Return a collection factory."""

    def _get_collection(name, fixes=False, **kwargs):
        return Collection.from_dir(f"t/data/{name}/", fixes, **kwargs)

    return _get_collection


################################################################################


def pytest_addoption(parser) -> None:
    parser.addoption("--runslow", action="store_true", default=False, help="run slow tests")


def pytest_configure(config) -> None:
    config.addinivalue_line("markers", "slow: mark test as slow to run")


def pytest_collection_modifyitems(config, items) -> None:
    if config.getoption("--runslow"):
        # --runslow given in cli: do not skip slow tests
        return
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)
