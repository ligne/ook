# vim: ts=4 : sw=4 : et

import nose
from nose.tools import *
from xml.etree import ElementTree
import datetime

import pandas as pd

import reading.goodreads

def test_process_review():
    r = ElementTree.parse('tests/data/review/1629171100.xml')
    eq_(reading.goodreads.process_review(r), {
        'Author Id': 12476,
        'Author': 'Joe Haldeman',
        'AvgRating': 4.15,
        'Binding': 'Paperback',
        'Book Id': 13629345,
        'Borrowed': False,
        'Added': pd.Timestamp('2016-05-04'),
        'Read': pd.Timestamp(None),
        'Started': pd.Timestamp(None),
        'Shelf': 'pending',
        'Rating': 0,
        'Pages': 240,
        'Scheduled': pd.Timestamp(None),
        'Title': 'The Forever War',
        'Work': 423,
    })

    r = ElementTree.parse('tests/data/review/1926519212.xml')
    eq_(reading.goodreads.process_review(r), {
        'Author Id': 9121,
        'Author': 'James Fenimore Cooper',
        'AvgRating': 3.37,
        'Binding': 'Paperback',
        'Book Id': 38290,
        'Borrowed': False,
        'Added': pd.Timestamp('2017-02-27'),
        'Read': pd.Timestamp(None),
        'Started': pd.Timestamp(None),
        'Shelf': 'pending',
        'Rating': 0,
        'Pages': 496,
        'Scheduled': pd.Timestamp('2018'),
        'Title': 'The Pioneers',
        'Work': 443966,
    })

    r = ElementTree.parse('tests/data/review/1977161022.xml')
    nose.tools.eq_(reading.goodreads.process_review(r), {
        'Author Id': 143840,
        'Author': u'Françoise Mallet-Joris',
        'AvgRating': 3.51,
        'Binding': 'Mass Market Paperback',
        'Book Id': 34910673,
        'Borrowed': True,
        'Added': pd.Timestamp('2017-04-20'),
        'Read': pd.Timestamp(None),
        'Started': pd.Timestamp(None),
        'Shelf': 'pending',
        'Rating': 0,
        'Pages': 242,
        'Scheduled': pd.Timestamp(None),
        'Title': u'Le rempart des béguines',
        'Work': 238317,
    })


def test__parse_book_api():
    r = ElementTree.parse('tests/data/book/115069.xml')
    nose.tools.eq_(reading.goodreads._parse_book_api(r), {
        'Language': 'fr',
        'Published': 1891,
        'Series Id': 40441,
        'Series': 'Les Rougon-Macquart',
        'Entry': '18',
        'Category': 'novels',
#        'Genres': '',
    })

    r = ElementTree.parse('tests/data/book/3602116.xml')
    nose.tools.eq_(reading.goodreads._parse_book_api(r), {
        'Language': 'en',
        'Published': 397,
        'Series Id': None,
        'Series': None,
        'Entry': None,
        'Category': 'non-fiction',
#        'Genres': '',
    })

    r = ElementTree.parse('tests/data/book/38290.xml')
    nose.tools.eq_(reading.goodreads._parse_book_api(r), {
        'Language': None,
        'Published': 1823,
        'Series Id': 81550,
        'Series': 'The Leatherstocking Tales',
        'Entry': '1',
        'Category': 'novels',
#        'Genres': '',
    })

    r = ElementTree.parse('tests/data/book/17999159.xml')
    nose.tools.eq_(reading.goodreads._parse_book_api(r), {
        'Language': 'en',
        'Published': 2013,
        'Series Id': None,
        'Series': None,
        'Entry': None,
        'Category': 'non-fiction',  # FIXME should be 'graphic'
#        'Genres': '',
    })


def test__parse_series():
    r = ElementTree.parse('tests/data/series/40441.xml')
    nose.tools.eq_(reading.goodreads._parse_series(r), {
        'Series': 'Les Rougon-Macquart',
        'Count': '20',
        'Entries': ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '1-4', '5-8'],
    })


