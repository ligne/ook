# vim: ts=4 : sw=4 : et

import pandas as pd
import pytest

from reading.graph import _days_remaining


@pytest.mark.parametrize(
    "year,today,expected",
    [
        # current normal year:
        (2022, "2022-01-01", 365),
        (2022, "2022-12-31", 1),
        # current leap year
        (2024, "2024-01-01", 366),
        (2024, "2024-12-31", 1),
        # different year
        (2022, "2023-12-21", 365),  # normal year
        (2024, "2023-12-21", 366),  # leap year
        # part-way through the year
        (2022, "2022-02-28", 307),  # normal year
        (2024, "2024-02-29", 307),  # leap year
    ],
)
def test_days_remaining(year, today, expected) -> None:
    assert _days_remaining(year, pd.Timestamp(today)) == expected
