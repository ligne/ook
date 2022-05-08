# vim: ts=4 : sw=4 : et

"""Code for scheduling books."""

import itertools

import pandas as pd

from .chain import Chain
from .chain import _dates as chain_dates
from .chain import _windows


TODAY = pd.Timestamp.today()

# use cases:
#   reading through an author (Haruki Murakami)
#   with an offset into the year (Iain M. Banks)
#   reading a series (Rougon-Macquart)
#   series with missing volumes -- both strict and break
#   reading several books a year (Discworld)

# used by:
#   suggestions.py in scheduled mode
#       year for $date only
#       might want to filter
#   lint.py
#       no filtering, just check
#   reading.py
#       identifying books for each scheduled year


# pylint: disable=too-many-arguments
def _schedule(
    df,
    author=None,
    series=None,
    start=None,
    per_year=1,
    offset=0,
    force=False,
    skip=0,
    date=TODAY,
):
    if author:
        series = Chain.from_author_name(df, author)
    elif series:
        series = Chain.from_series_name(df, series)

    if not start:
        start = date.year

    dates = _dates(
        start,
        per_year,
        offset,
        force,
        last_read=series.last_read,
        date=date,
    )

    dates = itertools.islice(dates, skip, None)

    return zip(dates, series.remaining.index)


# converts a stream of windows into a stream of dates for scheduling
def _dates(
    start,
    per_year=1,
    offset=1,
    force=False,
    last_read=None,
    date=TODAY,
):
    yield from chain_dates(
        _windows(start, per_year, offset),
        per_year=per_year,
        force=force,
        last_read=last_read,
        date=date,
    )


# pylint: enable=too-many-arguments


################################################################################


def main():  # pragma: no cover
    from .collection import Collection
    from .config import Config

    config = Config.from_file()
    schedules = config("scheduled")

    c = Collection.from_dir().shelves(exclude=["kindle", "to-read"])
    c.set_schedules(schedules)

    df = c.df

    for schedule in schedules:
        # find the books
        title = schedule.get("author") or schedule.get("series")
        if "author" in schedule:
            chain = Chain.from_author_name(df, schedule.pop("author"))
        elif "series" in schedule:
            chain = Chain.from_series_name(df, schedule.pop("series"))

        # schedule using the other arguments
        book_ids, _ = zip(*chain.schedule(**schedule))
        print(title)
        for book_id in book_ids:
            print(
                "{book.Scheduled:%F} {book.Title} ({book.Published:.0f})".format(
                    book=df.loc[book_id]
                )
            )
        print()

    print("----")
    print("This year:")
    date = pd.Timestamp(f"{TODAY.year}-12-31")
    for book in c.scheduled_at(date).df.sort_values("Title").itertuples():
        print(" *", book.Title)
    print("----")

    c.reset()

    print("Next year:")
    date = pd.Timestamp(f"{TODAY.year+1}-12-31")
    for book in c.scheduled_at(date).df.sort_values("Title").itertuples():
        print(" *", book.Title)
    print("----")

    c.reset()

    print("CURRENT:")
    date = pd.Timestamp.now()
    for book in c.scheduled_at(date).df.sort_values("Title").itertuples():
        print(" *", book.Title)


if __name__ == "__main__":
    main()
