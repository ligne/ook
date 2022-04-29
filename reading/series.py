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


# whether to ignore the series.
def ignore(series_id):
    return int(series_id) in config("series.ignore")
