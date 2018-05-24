# vim: ts=4 : sw=4 : et

import nose
from xml.etree import ElementTree

import reading.goodreads

def test_process_book():
    r = ElementTree.parse('tests/data/review/1629171100.xml')
    nose.tools.eq_(reading.goodreads.process_book(r), {
        'Author': 'Joe Haldeman',
        'Author Id': '12476',
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
        'Scheduled': '',
        'Borrowed': 'False',
    })

    r = ElementTree.parse('tests/data/review/1926519212.xml')
    nose.tools.eq_(reading.goodreads.process_book(r), {
        'Author': 'James Fenimore Cooper',
        'Author Id': '9121',
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
        'Scheduled': '2018',
        'Borrowed': 'False',
    })

    r = ElementTree.parse('tests/data/review/1977161022.xml')
    nose.tools.eq_(reading.goodreads.process_book(r), {
        'Author Id': '143840',
        'Author': u'Françoise Mallet-Joris',
        'Average Rating': '3.51',
        'Binding': 'Mass Market Paperback',
        'Book Id': 34910673,
        'Bookshelves': 'borrowed, pending',
        'Borrowed': 'True',
        'Date Added': '2017/04/20',
        'Date Read': '',
        'Date Started': '',
        'Exclusive Shelf': 'pending',
        'My Rating': '0',
        'Number of Pages': '242',
        'Scheduled': '',
        'Title': u'Le rempart des béguines',
        'Work Id': '238317',
    })


def test__parse_book_api():
    r = ElementTree.parse('tests/data/book/115069.xml')
    nose.tools.eq_(reading.goodreads._parse_book_api(r), {
        'Language': 'fr',
        'Original Publication Year': '1891',
        'Series Id': '40441',
        'Series': 'Les Rougon-Macquart',
        'Entry': '18',
#        'Category': 'novel',
#        'Genres': '',
    })

    r = ElementTree.parse('tests/data/book/3602116.xml')
    nose.tools.eq_(reading.goodreads._parse_book_api(r), {
        'Language': 'en',
        'Original Publication Year': '397',
        'Series Id': None,
        'Series': None,
        'Entry': None,
#        'Category': 'non-fiction',
#        'Genres': '',
    })

