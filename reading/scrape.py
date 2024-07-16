# vim: ts=4 : sw=4 : et

"""Scrape information that's in the goodreads books list but missing from the API(!!)."""

from __future__ import annotations

import datetime
import re
from typing import Optional

import bs4
from bs4 import BeautifulSoup
from dateutil import parser as du_parser  # https://github.com/python/typeshed/issues/9377
import pandas as pd


#################################################################################


def book_id(review: bs4.element.Tag) -> int:
    return int(
        re.search(
            r"/book/show/(\d+)",
            review.find_all(class_="title")[0].div.a["href"],
        ).group(1)
    )


def pages(review: bs4.element.Tag) -> Optional[int]:
    if m := re.search(r"[\d,]+", review.find(class_="num_pages").div.text):
        return int(m.group(0).replace(",", ""))
    return None


def binding(review: bs4.element.Tag) -> Optional[str]:
    """Return the binding from $review, if present."""
    if elem := review.find(class_="format"):
        return next(elem.div.stripped_strings, None)
    return None


def started_date(review: bs4.element.Tag) -> Optional[datetime.date]:
    return _get_date(review, "date_started_value")


def read_date(review: bs4.element.Tag) -> Optional[datetime.date]:
    return _get_date(review, "date_read_value")


def _get_date(review: bs4.element.Tag, field: str) -> Optional[datetime.date]:
    if date_tag := review.find("span", class_=field):
        return du_parser.parse(
            date_tag.text,
            default=datetime.datetime(2018, 1, 1),
        )
    return None


################################################################################


def _scrape(fname: str) -> pd.DataFrame:
    with open(fname) as fh:
        soup = BeautifulSoup(fh, "lxml")

    books = []

    for review in soup.find_all(id=re.compile(r"^review_\d+")):
        books.append(
            {
                "BookId": book_id(review),
                "Started": started_date(review),
                "Read": read_date(review),
                "Pages": pages(review),
                "Binding": binding(review),
            }
        )

    # remove the duplicates
    fix_df = pd.DataFrame(books).set_index("BookId")
    return fix_df[~fix_df.index.duplicated()]


def _rebuild(base: pd.DataFrame, old: pd.DataFrame, new: pd.DataFrame) -> pd.DataFrame:
    fixes = base.copy()  # copy just to be safe

    # add the old data first, so it's possible to update from only a subset of
    # the books (since the goodreads page is slow to load in its entirety)
    #
    # FIXME just want base.isnull() for non-date columns? otherwise can
    # overwrite more recent data from the API. fixes.update(overwrite=False)
    # would do this.
    #
    # FIXME the started/read dates are no longer as useful as they used to be,
    # since the API started reflecting the dates set in the review, rather than
    # the points when that book was marked currently-reading/read.
    fixes.update(old)
    fixes.update(new)

    # remove no-op changes and empty bits
    return fixes.where(base != fixes).dropna(how="all", axis="index")


def scrape(path: str, old: pd.DataFrame, base: pd.DataFrame) -> pd.DataFrame:
    """Return an overlay for the goodreads table scraped from the HTML at $path."""
    return _rebuild(base, old, new=_scrape(path))
