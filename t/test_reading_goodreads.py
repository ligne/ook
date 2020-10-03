# vim: ts=4 : sw=4 : et

from xml.etree import ElementTree

import pandas as pd

import reading.goodreads
from reading.goodreads import (
    _get_authors,
    _get_category,
    _get_entry,
    _parse_book_series,
    _parse_entries,
    _parse_series,
)


def test_process_review():
    r = ElementTree.parse('t/data/review/1629171100.xml')
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

    r = ElementTree.parse('t/data/review/1926519212.xml')
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

    r = ElementTree.parse('t/data/review/1977161022.xml')
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
    r = ElementTree.parse('t/data/book/115069.xml')
    assert reading.goodreads._parse_book_api(r) == {
        'Author': 'Émile Zola',
        'AuthorId': 4750,
        'Title': "L'Argent",
        'Language': 'fr',
        'Published': 1891,
        'Pages': 542.,
        'Category': 'novels',
    }

    r = ElementTree.parse('t/data/book/3602116.xml')
    assert reading.goodreads._parse_book_api(r) == {
        'Author': 'Augustine of Hippo',
        'AuthorId': 6819578,
        'Title': 'Confessions',
        'Language': 'en',
        'Published': 397,
        'Pages': 311,
        'Category': 'non-fiction',
    }

    r = ElementTree.parse('t/data/book/38290.xml')
    assert reading.goodreads._parse_book_api(r) == {
        'Author': 'James Fenimore Cooper',
        'AuthorId': 9121,
        'Title': 'The Pioneers (Leatherstocking Tales, #4)',
        'Language': None,
        'Published': 1823,
        'Pages': 496,
        'Category': 'novels',
    }

    r = ElementTree.parse('t/data/book/17999159.xml')
    assert reading.goodreads._parse_book_api(r) == {
        'Author': 'Allie Brosh',
        'AuthorId': 6984726,
        'Title': 'Hyperbole and a Half: Unfortunate Situations, Flawed Coping '
                 'Mechanisms, Mayhem, and Other Things That Happened',
        'Language': 'en',
        'Published': 2013,
        'Pages': 369,
        'Category': 'non-fiction',  # FIXME should be 'graphic'
    }


def test__parse_book_series():
    r = ElementTree.parse("t/data/book/115069.xml")
    assert _parse_book_series(r, []) == {
        "SeriesId": 40441,
        "Series": "Les Rougon-Macquart",
        "Entry": "18",
    }, "Parse series information from a book"

    r = ElementTree.parse("t/data/book/3602116.xml")
    assert _parse_book_series(r, []) is None, "Book without series"

    r = ElementTree.parse("t/data/book/38290.xml")
    assert _parse_book_series(r, []) == {
        "SeriesId": 55486,
        "Series": "The Leatherstocking Tales",
        "Entry": "4",
    }, "Book with multiple series"

    r = ElementTree.parse("t/data/book/38290.xml")
    assert _parse_book_series(r, [55486]) == {
        "SeriesId": 81550,
        "Series": "The Leatherstocking Tales",
        "Entry": "1",
    }, "Book ignoring one of the series"

    r = ElementTree.parse("t/data/book/68041.xml")
    assert _parse_book_series(r, []) == {
        "Entry": "1|2|3|4",
        "Series": "Earthsea Cycle",
        "SeriesId": 40909,
    }, "Book with multiple entries"


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
    assert (
        _get_authors([("Ernst Zillekens", "675893", "Editor")]) == ()
    ), "Just an editor"

    assert (
        _get_authors(
            [
                ("Brian Davies", "91422", "Editor"),
                ("Paul Kucharski", "14879133", "Editor"),
            ]
        )
        == ()
    ), "Just two editors"

    assert (
        _get_authors(
            [
                ("Helen Waddell", "132162", "translator"),
                ("M. Basil Pennington", "30605", "Introduction"),
            ]
        )
        == ()
    ), "Just a translator"

    assert (
        _get_authors(
            [
                ("Michael Cox", "39412", "Editor"),
                ("R.A. Gilbert", "1952887", "Editor"),
                ("Mrs. Henry Wood", "1779542", "Contributor"),
                ("Mary Elizabeth Braddon", "45896", "Contributor"),
            ]
        )
        == ()
    ), "An anthology, with editors and contributors"

    # include the author for graphic novels?
    assert _get_authors(
        [("Fabien Vehlmann", "761380", None), ("Kerascoët", "752696", "Illustrator")]
    ) == ("Fabien Vehlmann", "761380")


def test__get_category():
    assert _get_category([]) == "", "No shelves"
    assert _get_category(["short-stories"]) == "short-stories", "Shelf is the category name"
    assert _get_category(["something", "short-stories"]) == "short-stories", "Not the first shelf"
    assert _get_category(["essays"]) == "non-fiction", "Not the category name"

    assert _get_category(["blah", "linguistics"]) == "non-fiction", "Had to make a guess"


def test__parse_series():
    r = ElementTree.parse("t/data/series/40441.xml")
    assert _parse_series(r) == {
        "Series": "Les Rougon-Macquart",
        "Count": "20",
        "Entries": [str(x + 1) for x in range(20)],
    }, "Parsed a normal series"


def test__get_entry():
    assert _get_entry("1") == 1
    assert _get_entry("3") == 3
    assert _get_entry("1.1") is None
    assert _get_entry("1 of 2") == 1


def test__parse_entries():
    assert _parse_entries("1") == [1]
    assert _parse_entries("1-2") == [1, 2]
    assert _parse_entries("2-4") == [2, 3, 4]
    assert _parse_entries("2-4 ") == [2, 3, 4]
    assert _parse_entries("0") == [0]
    assert _parse_entries("0-2") == [0, 1, 2]

    assert _parse_entries("1, 2") == [1, 2]
    assert _parse_entries("1,2") == [1, 2]
    assert _parse_entries("1 & 2") == [1, 2]
    assert _parse_entries("1&2") == [1, 2]
    assert _parse_entries("1 & 3") == [1, 3]
    assert _parse_entries("1, 2 & 4") == [1, 2, 4]
    assert _parse_entries("1, 2, 4") == [1, 2, 4]
    assert _parse_entries("1-3 , 5") == [1, 2, 3, 5]
    assert _parse_entries("1-3 & 5") == [1, 2, 3, 5]
    assert _parse_entries("1-4, 6-7") == [1, 2, 3, 4, 6, 7]

    assert _parse_entries(None) == []
    assert _parse_entries("") == []
    assert _parse_entries(123) == []
    assert _parse_entries(1.3) == []

    # extra cruft
    assert _parse_entries("1-3 omnibus") == [1, 2, 3]
    assert _parse_entries("1 part 1") == [1]
    assert _parse_entries("1.3 (Monarch of the Glen)") == []
    assert _parse_entries("1 of 2") == [1]
    assert _parse_entries("2 of 2") == [2]
    assert _parse_entries("I") == []
    assert _parse_entries("3 pt. 2") == [3]
    assert _parse_entries("11B") == [11]
    assert _parse_entries("1, part 2 of 2") == [1]
    assert _parse_entries("2 (1/2)") == [2]
    assert _parse_entries("3 part 2/2") == [3]
    assert _parse_entries("Short Stories") == []

    # dotted entries
    assert _parse_entries("0.5") == []
    assert _parse_entries("0.5, 0.6") == []
    assert _parse_entries("0.5-0.6") == []
    assert _parse_entries("1-3, 3.1") == [1, 2, 3]
    assert _parse_entries("4, 5.2 & 13 ") == [4, 13]
