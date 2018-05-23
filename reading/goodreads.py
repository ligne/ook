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


# load the config to get the GR API key.
with open('data/config.yml') as fh:
    config = yaml.load(fh)


# get all the books on the goodread shelves.
def get_books():
    page = 1
    books = []

    while True:
        r = requests.get('https://www.goodreads.com/review/list/10052745.xml', params={
            'key': config['GR Key'],
#            'shelf': 'read',
            #'sort': 'date_added',
            'v': 2,
            'per_page': 200,
            'page': page,
        })
        time.sleep(1)

        x = ElementTree.fromstring(r.content)
        r = x.find('reviews')
        books += [ process_book(r) for r in x.findall('reviews/') ]

        if r.get('end') >= r.get('total'):
            break

        page += 1

    return pd.DataFrame(data=books)


# extract the interesting information from an xml blob, as a hash.
def process_book(r):
    if r.find('started_at').text:
        date_started = parse(r.find('started_at').text).strftime('%Y/%m/%d')
    else:
        date_started = ''

    if r.find('read_at').text:
        date_read = parse(r.find('read_at').text).strftime('%Y/%m/%d')
    else:
        date_read = ''

    series = entry = None

    title = r.find('book/title_without_series').text
    ftitle = r.find('book/title').text

    if title != ftitle:
        t = ftitle[len(title)+1:]
        m = re.match('\((?P<Series>.+?),? +#(?P<Entry>\d+)', t)
        if m:
            series = m.group('Series')
            entry = m.group('Entry')

    row = {
        'Book Id': int(r.find('book/id').text),
        'Work Id': r.find('book/work/id').text,
        'Author': re.sub(' +', ' ', r.find('book/authors/*').find('name').text),
        'Author Id': ', '.join([ a.find('id').text for a in r.findall('book/authors/author') ]),
        'Title': title,
        'Date Added': parse(r.find('date_added').text).strftime('%Y/%m/%d'),
        'Date Started': date_started,
        'Date Read': date_read,
        'Number of Pages': r.find('book/num_pages').text,
        'Average Rating': r.find('book/average_rating').text,
        'My Rating': r.find('rating').text,
        'Exclusive Shelf': r.find('shelves/shelf[@exclusive=\'true\']').get('name'),
        'Bookshelves': ', '.join(sorted([ s.get('name') for s in r.findall('shelves/shelf') ])),
        'Binding': r.find('book/format').text,
        'Series': series,
        'Entry': entry,
        'Scheduled': ', '.join([ s.get('name') for s in r.findall('shelves/') if re.match('^\d{4}$', s.get('name')) ]),
        'Borrowed': str(bool(r.findall('shelves/shelf[@name=\'borrowed\']'))),
    }

    return row


# information that's only available through the book-specific endpoints.
def fetch_book(book_id):
    book = _parse_book_api(_fetch_book_api(book_id))
    # if the interesting information isn't there, fetch it via html
    if False:
        _book = _parse_book_html(_fetch_book_html(book_id))

    # FIXME merge them

    return book


def _fetch_book_api(book_id):
    r = requests.get('https://www.goodreads.com/book/show/{}.xml'.format(book_id), params={
        'key': config['GR Key'],
    })
    return ElementTree.fromstring(r.content)


def _parse_book_api(xml):
    lang = xml.find('book/language_code').text
    try:
        lang = lang[:2]
    except:
        lang = str(lang)

    # FIXME work out which one is preferred
    series = entry = series_id = None
    for s in xml.findall('book/series_works/series_work'):
        series = s.find('series/title').text.strip()
        entry = s.find('user_position').text
        series_id = s.find('series/id').text
        break

    # FIXME work out category and genres too

    return {
        'Language': lang,
        'Original Publication Year': xml.find('book/work/original_publication_year').text,
        'Series': series,
        'Series Id': series_id,
        'Entry': entry,
    }


# the edition language isn't accessible through the API for some books.
def _fetch_book_html(book_id):
    pass


def _parse_book_html(html):
    pass


if __name__ == "__main__":
    r = ElementTree.parse('tests/data/review/1926519212.xml')
    print(process_book(r))

