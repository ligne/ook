# vim: ts=4 : sw=4 : et

from xml.etree import ElementTree
import pandas as pd

import reading.goodreads


def test_process_review():
    r = ElementTree.parse('tests/data/review/1629171100.xml')
    assert reading.goodreads.process_review(r) == {
        'AuthorId': 12476,
        'Author': 'Joe Haldeman',
        'AvgRating': 4.15,
        'Binding': 'Paperback',
        'BookId': 13629345,
        'Borrowed': False,
        'Added': pd.Timestamp('2016-05-04'),
        'Read': pd.Timestamp(None),
        'Started': pd.Timestamp(None),
        'Shelf': 'pending',
        'Rating': 0,
        'Scheduled': pd.Timestamp(None),
        'Title': 'The Forever War',
        'Work': 423,
    }

    r = ElementTree.parse('tests/data/review/1926519212.xml')
    assert reading.goodreads.process_review(r) == {
        'AuthorId': 9121,
        'Author': 'James Fenimore Cooper',
        'AvgRating': 3.37,
        'Binding': 'Paperback',
        'BookId': 38290,
        'Borrowed': False,
        'Added': pd.Timestamp('2017-02-27'),
        'Read': pd.Timestamp(None),
        'Started': pd.Timestamp(None),
        'Shelf': 'pending',
        'Rating': 0,
        'Scheduled': pd.Timestamp('2018'),
        'Title': 'The Pioneers',
        'Work': 443966,
    }

    r = ElementTree.parse('tests/data/review/1977161022.xml')
    assert reading.goodreads.process_review(r) == {
        'AuthorId': 143840,
        'Author': 'Françoise Mallet-Joris',
        'AvgRating': 3.51,
        'Binding': 'Mass Market Paperback',
        'BookId': 34910673,
        'Borrowed': True,
        'Added': pd.Timestamp('2017-04-20'),
        'Read': pd.Timestamp(None),
        'Started': pd.Timestamp(None),
        'Shelf': 'pending',
        'Rating': 0,
        'Scheduled': pd.Timestamp(None),
        'Title': u'Le rempart des béguines',
        'Work': 238317,
    }


def test__parse_book_api():
    r = ElementTree.parse('tests/data/book/115069.xml')
    assert reading.goodreads._parse_book_api(r) == {
        'Author': 'Émile Zola',
        'AuthorId': 4750,
        'Title': "L'Argent",
        'Language': 'fr',
        'Published': 1891,
        'Pages': 542.,
        'SeriesId': 40441,
        'Series': 'Les Rougon-Macquart',
        'Entry': '18',
        'Category': 'novels',
    }

    r = ElementTree.parse('tests/data/book/3602116.xml')
    assert reading.goodreads._parse_book_api(r) == {
        'Author': 'Augustine of Hippo',
        'AuthorId': 6819578,
        'Title': 'Confessions',
        'Language': 'en',
        'Published': 397,
        'Pages': 311,
        'SeriesId': None,
        'Series': None,
        'Entry': None,
        'Category': 'non-fiction',
    }

    r = ElementTree.parse('tests/data/book/38290.xml')
    assert reading.goodreads._parse_book_api(r) == {
        'Author': 'James Fenimore Cooper',
        'AuthorId': 9121,
        'Title': 'The Pioneers (Leatherstocking Tales, #4)',
        'Language': None,
        'Published': 1823,
        'Pages': 496,
        'SeriesId': 81550,
        'Series': 'The Leatherstocking Tales',
        'Entry': '1',
        'Category': 'novels',
    }

    r = ElementTree.parse('tests/data/book/17999159.xml')
    assert reading.goodreads._parse_book_api(r) == {
        'Author': 'Allie Brosh',
        'AuthorId': 6984726,
        'Title': 'Hyperbole and a Half: Unfortunate Situations, Flawed Coping Mechanisms, Mayhem, and Other Things That Happened',
        'Language': 'en',
        'Published': 2013,
        'Pages': 369,
        'SeriesId': None,
        'Series': None,
        'Entry': None,
        'Category': 'non-fiction',  # FIXME should be 'graphic'
    }


#def test__fetch_book_html():
#    ok_(reading.goodreads._fetch_book_html(819), 'Got output for an existing book')
#    eq_(reading.goodreads._fetch_book_html(1), None, "Nothing for a non-existing book, but it didn't explode")


def test__get_authors():
    assert reading.goodreads._get_authors(
        [('Agnes Owens', '108420', None)]
    ) == ('Agnes Owens', '108420'), 'One author'

    assert reading.goodreads._get_authors(
        [('Anton Chekhov', '5031025', None), ('Rosamund Bartlett', '121845', 'Translator')]
    ) == ('Anton Chekhov', '5031025'), 'With a role to ignore'

    assert reading.goodreads._get_authors(
        [('Wu  Ming', '191397', None)]
    ) == ('Wu Ming', '191397'), 'Spaces get squashed'

    assert reading.goodreads._get_authors(
        [('Cory Doctorow', '12581', None), ('Charles Stross', '8794', None)]
    ) == ('Cory Doctorow, Charles Stross', '12581, 8794'), 'Two authors'

    assert reading.goodreads._get_authors([
        ('John William Polidori', '26932', None),
        ('Robert  Morrison', '14558785', 'Editor'),
        ('Chris Baldick', '155911', 'Editor'),
        ('Letitia E. Landon', '2927201', None),
        ('J. Sheridan Le Fanu', '26930', None),
    ]) == (
        'John William Polidori, Letitia E. Landon, J. Sheridan Le Fanu',
        '26932, 2927201, 26930'
    ), 'Ignores editors of an anthology'

    assert reading.goodreads._get_authors(
        [('V.E. Schwab', '7168230', 'Pseudonym'), ('Victoria Schwab', '3099544', None)]
    ) == ('Victoria Schwab', '3099544'), 'Pseudonym as a separate name'

    assert reading.goodreads._get_authors(
        [('Victoria Schwab', '3099544', None), ('V.E. Schwab', '7168230', 'Pseudonym')]
    ) == ('Victoria Schwab', '3099544'), 'Pseudonyms listed afterwards'

    # FIXME editor(s)/translator but not other authors
    [('Ernst Zillekens', '675893', 'Editor')]
    [('Brian Davies', '91422', 'Editor'), ('Paul Kucharski', '14879133', 'Editor')]
    [('Helen Waddell', '132162', 'translator'), ('M. Basil Pennington', '30605', 'Introduction')]
    [
        ('Michael Cox', '39412', 'Editor'),
        ('R.A. Gilbert', '1952887', 'Editor'),
        ('Mrs. Henry Wood', '1779542', 'Contributor'),
        ('Mary Elizabeth Braddon', '45896', 'Contributor')
    ]

    # include the author for graphic novels?
    [('Fabien Vehlmann', '761380', None), ('Kerascoët', '752696', 'Illustrator')]


def test__parse_series():
    r = ElementTree.parse('tests/data/series/40441.xml')
    assert reading.goodreads._parse_series(r) == {
        'Series': 'Les Rougon-Macquart',
        'Count': '20',
        'Entries': [str(x + 1) for x in range(20)] + ['1-4', '5-8'],
    }, 'Parsed a normal series'


