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
        'Author': r.find('book/authors/*').find('name').text,
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

if __name__ == "__main__":
    r = ElementTree.parse('tests/data/review/1926519212.xml')
    print(process_book(r))

