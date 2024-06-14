# vim: ts=4 : sw=4 : et

"""Code for creating and operating on subsequences of books."""

from enum import Enum
import itertools

import attr
import pandas as pd


TODAY = pd.Timestamp.today()


class Order(Enum):
    """Sorting options for a Chain."""

    Series = 0
    Published = 1
    Added = 2


# missing books (for series only)
#   strict -- all books must be there; warn and leave gaps
#   ignore -- pretend gaps aren't there
#   break -- suspend when there's a gap.
# only trilogies need to be strict, so default to 'ignore'?
class Missing(Enum):
    """How to handle missing entries in a Series-based Chain."""

    Ignore = 0


################################################################################


def author_id_from_name(df, name):
    """Get the AuthorId from a name."""
    return list(df[df.Author.str.contains(name, na=False, regex=False)].AuthorId)[0]


def series_id_from_name(df, name):
    """Get the SeriesId from a name."""
    return list(df[df.Series.str.contains(name, na=False, regex=False)].SeriesId)[0]


# convert a list of entries as integers
def _entries_for_sorting(entry):
    return [int(x) for x in entry] if entry else None


################################################################################


@attr.s(kw_only=True)
class Chain:
    """An ordered group of books."""

    _df: pd.DataFrame = attr.ib(repr=lambda df: f"[{len(df)} books]")
    order: Order = attr.ib(default=Order.Published, repr=str)
    missing: Missing = attr.ib(default=Missing.Ignore, repr=str)

    ############################################################################

    @classmethod
    def from_series_id(cls, df, series_id, order=Order.Series, missing=Missing.Ignore):
        """Create from a SeriesId."""
        return cls(df=df[df.SeriesId == series_id], order=order, missing=missing)

    @classmethod
    def from_series_name(cls, df, name, order=Order.Series, missing=Missing.Ignore):
        """Create from a Series name."""
        series_id = series_id_from_name(df, name)
        return cls.from_series_id(df, series_id, order=order, missing=missing)

    @classmethod
    def from_author_id(cls, df, author_id, order=Order.Published):
        """Create from an AuthorId."""
        return cls(df=df[df.AuthorId == author_id], order=order, missing=Missing.Ignore)

    @classmethod
    def from_author_name(cls, df, name, order=Order.Published):
        """Create from an Author name."""
        author_id = author_id_from_name(df, name)
        return cls.from_author_id(df, author_id, order=order)

    ############################################################################

    @property
    def read(self):
        """Return a dataframe of books that have been read or are currently being read."""
        return self._df[self._df.Shelf.isin(["read", "currently-reading"])]

    @property
    def currently_reading(self):
        """Return whether any book is currently being read."""
        return (self._df.Shelf == "currently-reading").any()

    @property
    def last_read(self):
        """Return the date at which any of the books was last read (or today if still reading)."""
        if self.currently_reading:
            return pd.Timestamp("today")
        last_read = self.read.Read.max()
        return last_read if pd.notna(last_read) else None

    def sort(self):
        """Sort the books in-place."""
        if self.order == Order.Series:
            entries = self._df.Entry.str.split("|").apply(_entries_for_sorting)
            self._df = self._df.iloc[entries.argsort()]
        elif self.order == Order.Published:
            self._df = self._df.sort_values("Published")
        elif self.order == Order.Added:
            self._df = self._df.sort_values("Added")
        else:
            raise ValueError(f"Unknown sort option {self.order}")  # pragma: no cover

        return self

    @property
    def remaining(self):
        """Return a dataframe of the books that are still to be read, in the order to read them."""
        self.sort()
        return self._df[~self._df.Shelf.isin(["read", "currently-reading", "to-read"])]

    @property
    def readable(self):
        """Return a dataframe of readable books in order."""
        if self.missing == Missing.Ignore:
            return self.remaining
        raise ValueError(f"Unknown missing option {self.missing}")  # pragma: no cover

    ### Scheduling #############################################################

    def schedule(self, start=None, per_year=1, offset=0, force=False, skip=0):
        """Calculate a schedule for the books in this chain."""
        if not start:
            start = TODAY.year

        windows = _windows(start, per_year, offset)
        dates = _dates(
            windows,
            per_year=per_year,
            last_read=self.last_read,
            force=force,
            date=TODAY,
        )

        dates = itertools.islice(dates, skip, None)

        return zip(self.remaining.index, dates)


################################################################################


# converts a stream of windows into a stream of dates for scheduling
def _dates(
    windows,
    per_year,
    last_read,
    force,
    date,
):
    for window_start, window_end in windows:  # pragma: no branch
        # filter out windows that have passed
        if window_end < date:
            continue

        # check if it's been read
        if last_read:
            if last_read > window_start and not force:
                # skip to the next one.
                window_start, window_end = next(windows)  # pylint: disable=stop-iteration-return

            # fix up the first one if necessary
            next_read = last_read + pd.DateOffset(months=6)
            if per_year == 1 and next_read > window_start:
                window_start = next_read

        yield window_start
        break

    # return the start of remaining windows
    yield from (ii[0] for ii in windows)  # pragma: no branch


# returns a stream of (start, end) dates which may or may not want a book
# allocating to them, starting at the beginning of year $start
def _windows(start, per_year, offset):
    # needs to be a string or it thinks it's nanoseconds-since-epoch
    start = pd.Timestamp(str(start))

    interval = 12 // per_year  # FIXME use divmod and check?
    interval = pd.DateOffset(months=interval)

    if offset > 1:
        start += pd.DateOffset(months=offset - 1)

    while True:
        end = start + interval
        yield (start, end)
        start = end
