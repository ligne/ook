# vim: ts=4 : sw=4 : et

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
    return set(entry.split("|")) != set(series["Entries"])


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


# whether to ignore the series.
def ignore(series_id):
    return int(series_id) in config('series.ignore')
