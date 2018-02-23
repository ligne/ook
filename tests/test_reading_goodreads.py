# vim: ts=4 : sw=4 : et

import nose
from xml.etree import ElementTree

import reading.goodreads

def test_process_book():
    r = ElementTree.parse('tests/data/review/1629171100.xml')

    #self.assertEqual(reading.goodreads.process_book(r), {
    nose.tools.eq_(reading.goodreads.process_book(r), {
        'Author': 'Joe Haldeman',
        'Average Rating': '4.15',
        'Binding': 'Paperback',
        'Book Id': 13629345,
        'Bookshelves': 'pending',
        'Date Added': '2016/05/04',
        'Date Started': '',
        'Date Read': '',
        'Exclusive Shelf': 'pending',
        'My Rating': '0',
        'Number of Pages': '240',
        'Title': 'The Forever War',
        'Work Id': '423',
        'Series': None,
        'Entry': None,
        'Scheduled': None,
    })

    r = ElementTree.parse('tests/data/review/1926519212.xml')

    #assert reading.goodreads.process_book(r) == {
    nose.tools.eq_(reading.goodreads.process_book(r), {
        'Author': 'James Fenimore Cooper',
        'Average Rating': '3.37',
        'Binding': 'Paperback',
        'Book Id': 38290,
        'Bookshelves': '2018, pending',
        'Date Added': '2017/02/27',
        'Date Read': '',
        'Date Started': '',
        'Exclusive Shelf': 'pending',
        'My Rating': '0',
        'Number of Pages': '496',
        'Title': 'The Pioneers',
        'Work Id': '443966',
        'Series': 'Leatherstocking Tales',
        'Entry': '4',
        'Scheduled': '2018',
    })

