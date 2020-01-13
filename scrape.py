#!/usr/bin/python3

from bs4 import BeautifulSoup
import argparse
import datetime
import dateutil
import pandas as pd
import re

from reading.collection import Collection
from reading.config import config
from reading.compare import compare


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


# still a date, but from a different place in the html and pd.Timestamp may not
# be able to handle it. ValueError is to catch its NaT filler value.
def published(review):
    try:
        return dateutil.parser.parse(
            review.find(class_='date_pub').div.text,
            default=datetime.datetime(2018, 1, 1),
        ).year
    except (AttributeError, ValueError):
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
        soup = BeautifulSoup(fh, 'html5lib')

    books = []

    # FIXME scrape: fixed start/read dates, page-count
    for review in soup.find_all(id=re.compile(r'^review_\d+')):
        books.append({
            'BookId': book_id(review),
            'Started': started_date(review),
            'Read': read_date(review),
            'Pages': pages(review),
            # this doesn't seem to actually find anything...
            #'Published': published(review),
        })

    return pd.DataFrame(books).set_index('BookId')


def rebuild(scraped, df):
    # load the fixes file
    try:
        fixes = pd.read_csv('data/scraped.csv', index_col=0, parse_dates=[
            'Started',
            'Read',
        ])
    except FileNotFoundError:
        fixes = pd.DataFrame(columns=df.columns)

    for col in ['Started', 'Read']:
        if col in scraped:
            scraped[col] = pd.to_datetime(scraped[col])

    # merge in the new data
    fixes = pd.concat([
        fixes.loc[fixes.index.difference(scraped.index)],
        scraped,
    ], sort=False)

    # trim off scraped books that aren't being tracked
    fixes = fixes.loc[fixes.index.intersection(df.index)]

    # remove redundant fixes FIXME keeps throwing errors...
    check = df.loc[fixes.index].loc[:, fixes.columns]
#    fixes = fixes[check != fixes]

    return fixes.dropna(how='all').dropna(axis='columns', how='all').sort_index()


#################################################################################

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--ignore-changes', action='store_true')
    args = parser.parse_args()

    c = Collection(fixes=None)
    df = c.df

    old = Collection().df

    scraped = scrape(config('goodreads.html'))
    fixes = rebuild(scraped, df)

    if not args.ignore_changes:
        fixes.to_csv('data/scraped.csv', float_format='%.20g')

    new = Collection().df

    compare(old, new)


if __name__ == '__main__':
    main()


# vim: ts=4 : sw=4 : et
