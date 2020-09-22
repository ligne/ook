# vim: ts=4 : sw=4 : et

from functools import reduce
import operator

import reading.goodreads
from reading.goodreads import _parse_entries

from .config import config


# configuration:
#   series information cache.  build it from the series extracted from books.
#   series configuration.

# might be multiple volumes of the same work
#   subsume into volumes information

# use-cases
#   scheduling
#   handling book data
#   linting for missing books?
#   hiding blocked books


# books that should be hidden (because they're not the next in series or
# they're blocked by missing books.  should return a boolean pandas.Series so
# it can be used for slicing dataframes.
def hidden(_df):
    pass


# returns False if the series is deemed uninteresting.
def interesting(entry, series):
    book_entries = _parse_entries(entry)
    series_entries = reduce(operator.concat, [
        _parse_entries(x) for x in series['Entries']
    ])

    if set(book_entries) == set(series_entries):
        return False

    return True


# finds the series ID matching $name. throws an exception if there isn't
# exactly one.
def _lookup_series_id(df, name):
    series = df[df.Series.str.contains(name, na=False)]
    names = set(series.Series)

    if not names:
        raise ValueError("Couldn't find series matching {}".format(name))
    if len(names) > 1:
        raise ValueError("Ambiguous series name {}: {}".format(
            name, ', '.join(names)
        ))

    return int(series.SeriesId.iat[0])


# sort Entry strings
def _sort_entries(df):
    return df.loc[df.Entry.apply(_parse_entries).sort_values().index]


# whether to ignore the series.
def ignore(series_id):
    return int(series_id) in config('series.ignore')
