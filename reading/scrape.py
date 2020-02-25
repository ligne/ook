# vim: ts=4 : sw=4 : et

import datetime
import re
import dateutil
from bs4 import BeautifulSoup
import pandas as pd
from .storage import load_df


#################################################################################

def book_id(review):
    return int(re.search(
        r'/book/show/(\d+)',
        review.find_all(class_='title')[0].div.a['href']
    ).group(1))


def pages(review):
    try:
        return int(re.search(
            r'[\d,]+',
            review.find(class_='num_pages').div.text,
        ).group(0).replace(',', ''))
    except AttributeError:
        return None


def started_date(review):
    return _get_date(review, 'date_started_value')


def read_date(review):
    return _get_date(review, 'date_read_value')


def _get_date(review, field):
    try:
        return dateutil.parser.parse(
            review.find('span', class_=field).text,
            default=datetime.datetime(2018, 1, 1),
        )
    except AttributeError:
        return None


################################################################################

def scrape(fname):
    with open(fname) as fh:
        soup = BeautifulSoup(fh, "lxml")

    books = []

    for review in soup.find_all(id=re.compile(r'^review_\d+')):
        books.append({
            'BookId': book_id(review),
            'Started': started_date(review),
            'Read': read_date(review),
            'Pages': pages(review),
        })

    return pd.DataFrame(books).set_index('BookId')


def rebuild(scraped, df):
    # load the existing fixes
    fixes = load_df("scraped")

    # merge in the new data
    fixes = pd.concat([
        fixes.loc[fixes.index.difference(scraped.index)],
        scraped,
    ], sort=False)

    # trim off scraped books that aren't being tracked
    fixes = fixes.loc[fixes.index.intersection(df.index)]

    # remove no-op changes and empty bits
    #
    # FIXME just want df.isnull() for non-date columns? otherwise can
    # overwrite changes from the API
    return (
        fixes[df.reindex_like(fixes) != fixes]
        .dropna(how='all', axis='index')
        .dropna(how='all', axis='columns')
        .sort_index()
    )
