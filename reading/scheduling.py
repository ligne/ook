# vim: ts=4 : sw=4 : et

"""Code for scheduling books."""

import pandas as pd

from .chain import Chain
from .collection import Collection
from .config import Config


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


def main() -> None:  # pragma: no cover
    config = Config.from_file()
    schedules = config("scheduled")

    c = Collection.from_dir().shelves("kindle", "to-read", exclude=True)
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


if __name__ == "__main__":
    main()
