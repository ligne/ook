# vim: ts=4 : sw=4 : et

import sys
import operator
import re
from warnings import warn
from functools import reduce
import pandas as pd

from .config import config
from .collection import Collection
import reading.goodreads

# configuration:
#   series information cache.  build it from the series extracted from books.
#   series configuration.

# what to select
#   author
#   series
#   series ID
# what order to use
#   publication date
#   series order
#   random?
#   date added
# missing books (for series only)
#   strict -- all books must be there; warn and leave gaps
#   ignore -- pretend gaps aren't there
#   break -- suspend when there's a gap.
# only trilogies need to be strict, so default to 'ignore'?

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
def hidden(df):
    pass


# extracts a single entry from a string.
def _get_entry(string):
    # strip out the leading number and try and make it an int.
    try:
        m = re.match(r'\s*([\d.]+)', string)
        return int(m.group(0))
    except (ValueError, AttributeError):
        return


# converts an entries string into a list of integers
def _parse_entries(entries):
    if not isinstance(entries, str):
        return []

    if re.search('[,&]', entries):
        return reduce(operator.concat, [
            _parse_entries(x) for x in re.split('[,&]', entries)
        ])
    elif '-' in entries:
        start, end = [_get_entry(x) for x in entries.split('-')]
        if None not in (start, end):
            return list(range(start, end + 1))
        return []
    else:
        e = _get_entry(entries)
        return [e] if e is not None else []


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


# return the information for the series
# from cache and config?
def _get_series_settings(series):
    return {}


# return the series information (number of works and entry numbers)
def _get_series_info(series_id):
    return reading.goodreads._parse_series(
        reading.goodreads._fetch_series(series_id)
    ) or {}


# whether to ignore the series.
def ignore(series_id):
    return int(series_id) in config('series.ignore')


################################################################################

class Series():

    # FIXME need to filter out to-read books
    _df = Collection().df

    def __init__(self, author=None, series=None, series_id=None, settings=None, df=_df):
        # FIXME get settings for this series, and check
        if not settings:
            settings = _get_series_settings(series_id)

        if series and not series_id:
            # look up the series ID
            series_id = _lookup_series_id(df, series)

        if author:
            # just work through in order
            self.label = author
            self.order = settings.get('order', 'published')
            self.missing = 'ignore'
            self.df = df[df.Author.str.contains(author)]
        elif series_id:
            self.info = _get_series_info(series_id)
            self.series_id = series_id
            self.order = settings.get('order', 'series')
            self.missing = settings.get('missing', 'ignore')
            self.df = df[df.SeriesId == self.series_id].copy()
            self.label = self.info['Series']
        else:
            raise ValueError("Must provide author, series or series ID.")

        if self.df.duplicated('Work').any():
            warn('Duplicate works in series {}'.format(self.label))

    # books in the series that still need to be read
    def remaining(self):
        return self.sort().df[~self.df.Shelf.isin(['read', 'currently-reading'])]

    # return readable ones in order (for scheduling)
    def readable(self):
        if self.missing == 'ignore':
            return self.remaining()
        # if 'strict', return leaving gaps
        # if 'break', return until the first blockage

    # date this series was last read (today if still reading)
    def last_read(self):
        read = self.df[self.df.Read.notnull()]

        if len(self.df[self.df.Shelf == 'currently-reading']):
            return pd.Timestamp('today')
        elif len(read):
            return read.Read.sort_values().iat[-1]
        else:
            return None

    # sort the books according to preference
    def sort(self):
        if self.order == 'series':
            self.df = _sort_entries(self.df)
        elif self.order == 'published':
            self.df = self.df.sort_values('Published')
        elif self.order == 'random':
            self.df = self.df.loc[
                self.df.Title.apply(lambda x: x.__hash__()).sort_values().index
            ]
        return self


if __name__ == "__main__":
    (t, n) = sys.argv[1:3]
    if t == 'author':
        s = Series(author=n)
    elif t == 'series':
        s = Series(series=n)
    elif t == 'sid':
        s = Series(series_id=int(n))
    else:
        print("bad")
        sys.exit()

    print(s.remaining()[['Author', 'Series', 'Entry', 'Title']])

