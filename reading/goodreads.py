# vim: ts=4 : sw=4 : et

import sys
import time
import yaml
import datetime
import requests
import re
import pandas as pd
from xml.etree import ElementTree
from dateutil.parser import parse

import reading.series


# load the config to get the GR API key.
with open('data/config.yml') as fh:
    config = yaml.load(fh)


# get all the books on the goodread shelves.
def get_books():
    page = 1
    books = []

    while True:
        r = requests.get('https://www.goodreads.com/review/list/10052745.xml', params={
            'key': config['goodreads']['key'],
#            'shelf': 'read',
            #'sort': 'date_added',
            'v': 2,
            'per_page': 200,
            'page': page,
        })
        time.sleep(1)

        x = ElementTree.fromstring(r.content)

        for r in x.findall('reviews/'):
            book = process_review(r)
            book.update(fetch_book(book['Book Id']))
            books.append(book)

        r = x.find('reviews')
        if r.get('end') >= r.get('total'):
            break

        page += 1

        reading.cache.dump_yaml('series', reading.series.cache)

    return pd.DataFrame(data=books).set_index('Book Id')


# extract a (possibly missing) date.
def _get_date(xml, tag):
    date = xml.find(tag).text
    return pd.Timestamp(date and parse(date).date() or None)


# extract the interesting information from an xml review, as a hash.
def process_review(r):
    sched = [ s.get('name') for s in r.findall('shelves/') if re.match('^\d{4}$', s.get('name')) ]
    scheduled = pd.Timestamp(len(sched) and min(sched) or None)

    row = {
        'Book Id': int(r.find('book/id').text),
        'Work Id': int(r.find('book/work/id').text),
        'Author': re.sub(' +', ' ', r.find('book/authors/author').find('name').text),
        'Author Id': int(r.find('book/authors/author/id').text),
        'Title': r.find('book/title_without_series').text,
        'Date Added': _get_date(r, 'date_added'),
        'Date Started': _get_date(r, 'started_at'),
        'Date Read': _get_date(r, 'read_at'),
        'Number of Pages': float(r.find('book/num_pages').text or 'nan'),
        'Average Rating': float(r.find('book/average_rating').text),
        'My Rating': int(r.find('rating').text),
        'Exclusive Shelf': r.find('shelves/shelf[@exclusive=\'true\']').get('name'),
        'Bookshelves': ', '.join(sorted([ s.get('name') for s in r.findall('shelves/shelf') ])),
        'Binding': r.find('book/format').text,
        'Scheduled': scheduled,
        'Borrowed': bool(r.findall('shelves/shelf[@name=\'borrowed\']')),
    }

    return row


# information that's only available through the book-specific endpoints.
def fetch_book(book_id):
    book = _parse_book_api(_fetch_book_api(book_id))
    # if the interesting information isn't there, fetch it via html
    if False:
        book.update(_parse_book_html(_fetch_book_html(book_id)))

    # fetch series
    series_id = book['Series Id']
    if series_id:
        series = _parse_series(_fetch_series(series_id))
        reading.series.cache[series_id] = series

        if not reading.series.interesting(book['Entry'], series):
            # remove the series information
            book.update({
                'Series Id': None,
                'Series': None,
                'Entry': None,
            })

    return book


def _fetch_book_api(book_id):
    fname = 'data/cache/book/{}.xml'.format(book_id)
    try:
        with open(fname) as fh:
            xml = fh.read()
    except FileNotFoundError:
        xml = requests.get('https://www.goodreads.com/book/show/{}.xml'.format(book_id), params={
            'key': config['goodreads']['key'],
        }).content
        with open(fname, 'wb') as fh:
            fh.write(xml)
    return ElementTree.fromstring(xml)


def _parse_book_api(xml):
    lang = xml.find('book/language_code').text
    try:
        lang = lang[:2]
    except:
        pass

    series = entry = series_id = None
    for s in xml.findall('book/series_works/series_work'):
        if int(s.find('series/id').text) not in config['series']['ignore']:
            series_id = int(s.find('series/id').text)
            series = s.find('series/title').text.strip()
            entry = s.find('user_position').text
            break

    shelves = [s.get('name') for s in xml.findall('book/popular_shelves/')]

    return {
        'Language': lang,
        'Original Publication Year': float(xml.find('book/work/original_publication_year').text or 'nan'),
        'Series': series,
        'Series Id': series_id,
        'Entry': entry,
        'Category': _get_category(shelves),
    }


# the edition language isn't accessible through the API for some books.
def _fetch_book_html(book_id):
    pass


def _parse_book_html(html):
    pass


def _fetch_series(series_id):
    fname = 'data/cache/series/{}.xml'.format(series_id)
    try:
        with open(fname) as fh:
            xml = fh.read()
    except FileNotFoundError:
        xml = requests.get('https://www.goodreads.com/series/show/{}.xml'.format(series_id), params={
            'key': config['goodreads']['key'],
        }).content
        with open(fname, 'wb') as fh:
            fh.write(xml)
    return ElementTree.fromstring(xml)


def _parse_series(xml):
    return {
        'Series': xml.find('series/title').text.strip(),
        'Count': xml.find('series/primary_work_count').text,
        'Entries': [ x.find('user_position').text for x in xml.find('series/series_works') ],
    }


# tries to divine what sort of book this is based on the shelves.
def _get_category(shelves):
    patterns = (
        ('graphic', ('graphic-novels', 'comics', 'graphic-novel')),
        ('short-stories', ('short-stories', 'short-story', 'nouvelles', 'short-story-collections', 'relatos-cortos')),
        ('non-fiction', ('non-fiction', 'nonfiction', 'essays')),
        ('novel', ('novel', 'novels', 'roman', 'romans')),
    )

    for shelf in shelves:
        for (c, n) in patterns:
            if shelf in n:
                return c

    # if that failed, try and guess a sensible default
    patterns = (
        ('non-fiction', ('education', 'theology', 'linguistics')),
        ('novel', ('fiction')),
    )

    for shelf in shelves:
        for (c, n) in patterns:
            if shelf in n:
                return c

    return ''


if __name__ == "__main__":
    r = ElementTree.parse('tests/data/review/1926519212.xml')
    for f in sys.argv[1:]:
        r = ElementTree.parse(f)
        print(_parse_book_api(r)['Category'])
    #print(process_review(r))

