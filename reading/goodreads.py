# vim: ts=4 : sw=4 : et

"""Code for interacting with the Goodreads API."""

from functools import reduce
import operator
import re
from xml.etree import ElementTree
import time

from dateutil.parser import parse
import pandas as pd
import requests

from reading.config import category_patterns, config
from reading.series import interesting


# get all the books on the goodread shelves.
def get_books():
    page = 1
    books = []

    start_date = pd.Timestamp(config("goodreads.start"))

    while True:
        url = 'https://www.goodreads.com/review/list/{}.xml'.format(
            config('goodreads.user')
        )
        r = requests.get(url, params={
            'key': config('goodreads.key'),
            'v': 2,
            'per_page': 100,
            'page': page,
        })

        x = ElementTree.fromstring(r.content)

        for r in x.findall('reviews/'):
            book = process_review(r)

            if book["Read"] < start_date:
                continue

            api_book = fetch_book(book['BookId'])
            books.append({**api_book, **book})

        r = x.find('reviews')
        if int(r.get('end')) >= int(r.get('total')):
            break

        page += 1

        time.sleep(1)

    return pd.DataFrame(data=books).set_index("BookId")


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


################################################################################

# information that's only available through the book-specific endpoints.
def fetch_book(book_id):
    try:
        api_book = _fetch_book_api(book_id)
    except requests.exceptions.TooManyRedirects:
        print(f"Retrying {book_id}")
        api_book = _fetch_book_api(book_id)

    book = _parse_book_api(api_book)

    # fetch series information
    series_info = _parse_book_series(api_book, config("series.ignore"))
    if series_info:
        series = _parse_series(_fetch_series(series_info["SeriesId"]))
        if interesting(series_info["Entry"], series):
            book.update(series_info)

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
        time.sleep(1)
    return ElementTree.fromstring(xml)


def _parse_book_api(xml):
    lang = xml.find('book/language_code').text
    try:
        lang = lang[:2]
    except TypeError:
        pass

    shelves = [s.get('name') for s in xml.findall('book/popular_shelves/')]

#    _a = [(s.find('name').text, s.find('id').text, s.find('role').text)
#          for s in xml.findall('book/authors/author')]

    return {
        'Author': re.sub(' +', ' ', xml.find('book/authors/author/name').text),
        'AuthorId': int(xml.find('book/authors/author/id').text),
        'Title': xml.find('book/title').text,
        'Language': lang,
        'Published': float(xml.find('book/work/original_publication_year').text or 'nan'),
        'Pages': float(xml.find('book/num_pages').text or 'nan'),
        'Category': _get_category(shelves),
    }


def _parse_book_series(xml, ignore):
    for series in xml.findall("book/series_works/series_work"):
        series_id = int(series.find("series/id").text)
        series_name = series.find("series/title").text.strip()
        entry = series.find("user_position").text

        if entry and series_id not in ignore:
            return {
                "SeriesId": series_id,
                "Series": series_name,
                "Entry": "|".join((str(x) for x in _parse_entries(entry))),
            }
    return None


################################################################################

def _fetch_series(series_id):
    fname = 'data/cache/series/{}.xml'.format(series_id)
    try:
        with open(fname) as fh:
            xml = fh.read()
    except FileNotFoundError:
        xml = requests.get(f"https://www.goodreads.com/series/show/{series_id}.xml", params={
            'key': config('goodreads.key'),
        }).content
        with open(fname, 'wb') as fh:
            fh.write(xml)
    return ElementTree.fromstring(xml)


def _parse_series(xml):
    entries = []
    for work in xml.find("series/series_works"):
        entries.extend(_parse_entries(work.find("user_position").text))
    return {
        "Series": xml.find("series/title").text.strip(),
        "Count": xml.find("series/primary_work_count").text,
        "Entries": [str(x) for x in sorted(set(entries))],
    }


# extracts a single entry from a string.
def _get_entry(string):
    # strip out the leading number and try and make it an int.
    try:
        return int(re.match(r"\s*([\d.]+)", string).group(0))
    except (ValueError, AttributeError):
        return None


# converts an entries string into a list of integers
def _parse_entries(entries):
    if not isinstance(entries, str):
        return []

    if re.search("[,&]", entries):
        return reduce(operator.concat, [_parse_entries(x) for x in re.split("[,&]", entries)])
    elif "-" in entries:
        start, end = [_get_entry(x) for x in entries.split("-")]
        if None not in (start, end):
            return list(range(start, end + 1))
        return []
    else:
        e = _get_entry(entries)
        return [e] if e is not None else []


################################################################################

def _get_authors(authors):
    _authors = list(filter(lambda x: x[2] is None, authors))
    return (
        ', '.join([re.sub(r'\s+', ' ', a[0]) for a in _authors]),
        ', '.join([a[1] for a in _authors]),
    ) if _authors else ()


# tries to divine what sort of book this is based on the shelves.
def _get_category(shelves):
    for patterns in category_patterns():
        for shelf in shelves:
            for category in patterns:
                if shelf in category:
                    return category[0]

    return ""


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

