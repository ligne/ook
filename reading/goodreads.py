# vim: ts=4 : sw=4 : et

import requests
import re
import pandas as pd
from xml.etree import ElementTree
from dateutil.parser import parse

import reading.series
from reading.config import config


# get all the books on the goodread shelves.
def get_books():
    page = 1
    books = []

    while True:
        url = 'https://www.goodreads.com/review/list/{}.xml'.format(
            config('goodreads.user')
        )
        r = requests.get(url, params={
            'key': config('goodreads.key'),
            'v': 2,
            'per_page': 200,
            'page': page,
        })
        x = ElementTree.fromstring(r.content)

        for r in x.findall('reviews/'):
            book = process_review(r)
            api_book = fetch_book(book['BookId'])
            del api_book['Title']
            book.update(api_book)
            books.append(book)

        r = x.find('reviews')
        if r.get('end') >= r.get('total'):
            break

        page += 1

    df = pd.DataFrame(data=books).set_index('BookId')
    return df[~(df.Read < pd.Timestamp(config('goodreads.start')))]


# extract a (possibly missing) date.
def _get_date(xml, tag):
    date = xml.find(tag).text
    return pd.Timestamp(date and parse(date).date() or None)


# extract the interesting information from an xml review, as a hash.
def process_review(r):
    sched = [s.get('name') for s in r.findall('shelves/') if re.match(r'^\d{4}$', s.get('name'))]
    scheduled = pd.Timestamp(len(sched) and min(sched) or None)

    row = {
        'BookId': int(r.find('book/id').text),
        'Work': int(r.find('book/work/id').text),
        'Author': re.sub(' +', ' ', r.find('book/authors/author').find('name').text),
        'AuthorId': int(r.find('book/authors/author/id').text),
        'Title': r.find('book/title_without_series').text,
        'Added': _get_date(r, 'date_added'),
        'Started': _get_date(r, 'started_at'),
        'Read': _get_date(r, 'read_at'),
        'AvgRating': float(r.find('book/average_rating').text),
        'Rating': int(r.find('rating').text),
        'Shelf': r.find('shelves/shelf[@exclusive=\'true\']').get('name'),
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
    series_id = book['SeriesId']
    if series_id:
        series = _parse_series(_fetch_series(series_id))

        if not reading.series.interesting(book['Entry'], series):
            # remove the series information
            book.update({
                'SeriesId': None,
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
            'key': config('goodreads.key'),
        }).content
        with open(fname, 'wb') as fh:
            fh.write(xml)
    return ElementTree.fromstring(xml)


def _parse_book_api(xml):
    lang = xml.find('book/language_code').text
    try:
        lang = lang[:2]
    except TypeError:
        pass

    series = entry = series_id = None
    for s in xml.findall('book/series_works/series_work'):
        if int(s.find('series/id').text) not in config('series.ignore'):
            series_id = int(s.find('series/id').text)
            series = s.find('series/title').text.strip()
            entry = s.find('user_position').text
            break

    shelves = [s.get('name') for s in xml.findall('book/popular_shelves/')]

    _a = [(s.find('name').text, s.find('id').text, s.find('role').text)
          for s in xml.findall('book/authors/author')]

    return {
        'Author': re.sub(' +', ' ', xml.find('book/authors/author/name').text),
        'AuthorId': int(xml.find('book/authors/author/id').text),
        'Title': xml.find('book/title').text,
        'Language': lang,
        'Published': float(xml.find('book/work/original_publication_year').text or 'nan'),
        'Pages': float(xml.find('book/num_pages').text or 'nan'),
        'Series': series,
        'SeriesId': series_id,
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
            'key': config('goodreads.key'),
        }).content
        with open(fname, 'wb') as fh:
            fh.write(xml)
    return ElementTree.fromstring(xml)


def _parse_series(xml):
    return {
        'Series': xml.find('series/title').text.strip(),
        'Count': xml.find('series/primary_work_count').text,
        'Entries': [x.find('user_position').text for x in xml.find('series/series_works')],
    }


def _get_authors(authors):
    _authors = list(filter(lambda x: x[2] is None, authors))
    if len(_authors):
        return (
            ', '.join([re.sub(r'\s+', ' ', a[0]) for a in _authors]),
            ', '.join([a[1] for a in _authors]),
        )


# tries to divine what sort of book this is based on the shelves.
def _get_category(shelves):
    patterns = (
        ('graphic', ('graphic-novels', 'comics', 'graphic-novel')),
        ('short-stories', ('short-stories', 'short-story', 'nouvelles', 'short-story-collections', 'relatos-cortos')),
        ('non-fiction', ('non-fiction', 'nonfiction', 'essays')),
        ('novels', ('novel', 'novels', 'roman', 'romans')),
    )

    for shelf in shelves:
        for (c, n) in patterns:
            if shelf in n:
                return c

    # if that failed, try and guess a sensible default
    patterns = (
        ('non-fiction', ('education', 'theology', 'linguistics')),
        ('novels', ('fiction')),
    )

    for shelf in shelves:
        for (c, n) in patterns:
            if shelf in n:
                return c

    return ''


################################################################################

# search by title
def search_title(term):
    r = requests.get('https://www.goodreads.com/search/index.xml', params={
        'key': config('goodreads.key'),
        'search[field]': 'title',
        'q': term,
    })

    xml = ElementTree.fromstring(r.content)
    return [{
        'Title': x.find('best_book/title').text,
        'BookId': int(x.find('best_book/id').text),
        'Work': int(x.find('id').text),
        'AuthorId': x.find('best_book/author/id').text,
        'Author': x.find('best_book/author/name').text,
        'Published': x.find('original_publication_year').text,
        'Ratings': int(x.find('ratings_count').text),
    } for x in xml.findall('search/results/work')]


################################################################################

if __name__ == "__main__":
    pass

