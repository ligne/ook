# vim: ts=4 : sw=4 : et

import pandas as pd

from .config import df_columns, date_columns


def _load_csv(name, columns, parse_dates=False):
    try:
        return pd.read_csv(name, index_col=0, parse_dates=parse_dates)
    except FileNotFoundError:
        return pd.DataFrame(columns=columns)


def load_df(name, fname=None):
    return _load_csv(
        fname or f"data/{name}.csv",
        columns=df_columns(name),
        parse_dates=date_columns(name)
    )
