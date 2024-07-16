# vim: ts=4 : sw=4 : et

"""Loading and storing dataframes."""

from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import Dict, Optional, Union

import attr
import pandas as pd

from .config import date_columns, df_columns


def _load_csv(
    name: str,
    columns: list[str],
    parse_dates: Union[bool, list[str]] = False,
) -> pd.DataFrame:
    try:
        return pd.read_csv(name, index_col=0, parse_dates=parse_dates)
    except FileNotFoundError:
        return pd.DataFrame(columns=columns)


def load_df(name: str, fname: Optional[str] = None, dirname: Optional[str] = None) -> pd.DataFrame:
    """Load and return a dataframe of type $name, creating it if necessary."""
    if dirname:
        fname = f"{dirname}/{name}.csv"

    return _load_csv(
        fname or f"data/{name}.csv",
        columns=df_columns(name),
        parse_dates=date_columns(name),
    )


def save_df(name: str, df: pd.DataFrame, fname: Optional[Path] = None) -> None:
    """Save a dataframe of type $name in an aesthetic format."""
    df.sort_index().to_csv(
        fname or f"data/{name}.csv",
        columns=df_columns(name),
        float_format="%.20g",
    )


################################################################################


@attr.s
class Store:
    """Load and store data."""

    directory: Path = attr.ib(default=Path("data"), converter=Path, repr=str)
    _tables: Dict[str, pd.DataFrame] = attr.ib(factory=dict, init=False, repr=False)

    def _getter(self, name: str) -> pd.DataFrame:
        kind = name.split("-")[0]
        return self._tables.get(name, load_df(kind, fname=f"{self.directory}/{name}.csv"))

    # the arguments have to be in a strange order or partial does weird things with them
    def _setter(self, value: pd.DataFrame, name: str) -> None:
        self._tables[name] = value

    goodreads = property(
        partial(_getter, name="goodreads"),
        partial(_setter, name="goodreads"),
    )
    ebooks = property(
        partial(_getter, name="ebooks"),
        partial(_setter, name="ebooks"),
    )
    scraped = property(
        partial(_getter, name="scraped"),
        partial(_setter, name="scraped"),
    )
    authors = property(
        partial(_getter, name="authors"),
        partial(_setter, name="authors"),
    )
    books = property(
        partial(_getter, name="books"),
        partial(_setter, name="books"),
    )
    ebook_metadata = property(
        partial(_getter, name="metadata-ebooks"),
        partial(_setter, name="metadata-ebooks"),
    )
    gr_metadata = property(
        partial(_getter, name="metadata-gr"),
        partial(_setter, name="metadata-gr"),
    )

    def save(self, directory: Union[Path, str]) -> None:
        """Save the tables to $directory."""
        for name, table in self._tables.items():
            kind = name.split("-")[0]
            save_df(kind, table, f"{directory}/{name}.csv")
