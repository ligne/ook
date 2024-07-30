# vim: ts=4 : sw=4 : et

from __future__ import annotations

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
    interesting,
)


def test_process_review() -> None:
    r = ElementTree.parse("t/data/review/1629171100.xml")
    assert reading.goodreads.process_review(r) == {
        "AuthorId": 12476,
        "Author": "Joe Haldeman",
        "AvgRating": 4.15,
        "Binding": "Paperback",
        "BookId": 13629345,
        "Borrowed": False,
        "Added": pd.Timestamp("2016-05-04"),
        "Read": pd.Timestamp(None),
        "Started": pd.Timestamp(None),
        "Shelf": "pending",
        "Rating": 0,
        "Scheduled": pd.Timestamp(None),
        "Title": "The Forever War",
        "Work": 423,
    }

    r = ElementTree.parse("t/data/review/1926519212.xml")
    assert reading.goodreads.process_review(r) == {
        "AuthorId": 9121,
        "Author": "James Fenimore Cooper",
        "AvgRating": 3.37,
        "Binding": "Paperback",
        "BookId": 38290,
        "Borrowed": False,
        "Added": pd.Timestamp("2017-02-27"),
        "Read": pd.Timestamp(None),
        "Started": pd.Timestamp(None),
        "Shelf": "pending",
        "Rating": 0,
        "Scheduled": pd.Timestamp("2018"),
        "Title": "The Pioneers",
        "Work": 443966,
    }

    r = ElementTree.parse("t/data/review/1977161022.xml")
    assert reading.goodreads.process_review(r) == {
        "AuthorId": 143840,
        "Author": "Françoise Mallet-Joris",
        "AvgRating": 3.51,
        "Binding": "Mass Market Paperback",
        "BookId": 34910673,
        "Borrowed": True,
        "Added": pd.Timestamp("2017-04-20"),
        "Read": pd.Timestamp(None),
        "Started": pd.Timestamp(None),
        "Shelf": "pending",
        "Rating": 0,
        "Scheduled": pd.Timestamp(None),
        "Title": "Le rempart des béguines",
        "Work": 238317,
    }


def test__parse_book_api() -> None:
    r = ElementTree.parse("t/data/book/115069.xml")
    assert reading.goodreads._parse_book_api(r) == {
        "Author": "Émile Zola",
        "AuthorId": 4750,
        "Title": "L'Argent",
        "Language": "fr",
        "Published": 1891,
        "Pages": 542.0,
        "Category": "novels",
        "Work": 417025,
    }

    r = ElementTree.parse("t/data/book/3602116.xml")
    assert reading.goodreads._parse_book_api(r) == {
        "Author": "Augustine of Hippo",
        "AuthorId": 6819578,
        "Title": "Confessions",
        "Language": "en",
        "Published": 397,
        "Pages": 311,
        "Category": "non-fiction",
        "Work": 1427207,
    }

    r = ElementTree.parse("t/data/book/38290.xml")
    assert reading.goodreads._parse_book_api(r) == {
        "Author": "James Fenimore Cooper",
        "AuthorId": 9121,
        "Title": "The Pioneers (Leatherstocking Tales, #4)",
        "Language": None,
        "Published": 1823,
        "Pages": 496,
        "Category": "novels",
        "Work": 443966,
    }

    r = ElementTree.parse("t/data/book/17999159.xml")
    assert reading.goodreads._parse_book_api(r) == {
        "Author": "Allie Brosh",
        "AuthorId": 6984726,
        "Title": (
            "Hyperbole and a Half: Unfortunate Situations, Flawed Coping "
            "Mechanisms, Mayhem, and Other Things That Happened"
        ),
        "Language": "en",
        "Published": 2013,
        "Pages": 369,
        "Category": "non-fiction",  # FIXME should be 'graphic'
        "Work": 24510592,
    }


def test__parse_book_series() -> None:
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


def test__get_authors() -> None:
    assert reading.goodreads._get_authors(
        [
            ("Agnes Owens", "108420", None),
        ],
    ) == ("Agnes Owens", "108420"), "One author"

    assert reading.goodreads._get_authors(
        [
            ("Anton Chekhov", "5031025", None),
            ("Rosamund Bartlett", "121845", "Translator"),
        ],
    ) == ("Anton Chekhov", "5031025"), "With a role to ignore"

    assert reading.goodreads._get_authors(
        [
            ("Wu  Ming", "191397", None),
        ]
    ) == ("Wu Ming", "191397"), "Spaces get squashed"

    assert reading.goodreads._get_authors(
        [
            ("Cory Doctorow", "12581", None),
            ("Charles Stross", "8794", None),
        ]
    ) == ("Cory Doctorow, Charles Stross", "12581, 8794"), "Two authors"

    assert reading.goodreads._get_authors(
        [
            ("John William Polidori", "26932", None),
            ("Robert  Morrison", "14558785", "Editor"),
            ("Chris Baldick", "155911", "Editor"),
            ("Letitia E. Landon", "2927201", None),
            ("J. Sheridan Le Fanu", "26930", None),
        ]
    ) == (
        "John William Polidori, Letitia E. Landon, J. Sheridan Le Fanu",
        "26932, 2927201, 26930",
    ), "Ignores editors of an anthology"

    assert reading.goodreads._get_authors(
        [
            ("V.E. Schwab", "7168230", "Pseudonym"),
            ("Victoria Schwab", "3099544", None),
        ]
    ) == ("Victoria Schwab", "3099544"), "Pseudonym as a separate name"

    assert reading.goodreads._get_authors(
        [
            ("Victoria Schwab", "3099544", None),
            ("V.E. Schwab", "7168230", "Pseudonym"),
        ]
    ) == ("Victoria Schwab", "3099544"), "Pseudonyms listed afterwards"

    # FIXME editor(s)/translator but not other authors
    assert (
        _get_authors(
            [
                ("Ernst Zillekens", "675893", "Editor"),
            ]
        )
        == ()
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
        [
            ("Fabien Vehlmann", "761380", None),
            ("Kerascoët", "752696", "Illustrator"),
        ]
    ) == ("Fabien Vehlmann", "761380")


def test__get_category() -> None:
    assert _get_category([]) == "", "No shelves"
    assert _get_category(["short-stories"]) == "short-stories", "Shelf is the category name"
    assert _get_category(["something", "short-stories"]) == "short-stories", "Not the first shelf"
    assert _get_category(["essays"]) == "non-fiction", "Not the category name"

    assert _get_category(["blah", "linguistics"]) == "non-fiction", "Had to make a guess"


def test_interesting() -> None:
    assert interesting("1", {"Entries": ["1", "2", "3"]})
    assert not interesting("1", {"Entries": ["1"]})
    assert not interesting("1|2", {"Entries": ["1", "2"]})


def test__parse_series() -> None:
    r = ElementTree.parse("t/data/series/40441.xml")
    assert _parse_series(r) == {
        "Series": "Les Rougon-Macquart",
        "Count": "20",
        "Entries": [str(x + 1) for x in range(20)],
        "Works": {
            10242: "3",
            28958: "14",
            89633: "9",
            101404: "17",
            110658: "10",
            303087: "1",
            417025: "18",
            741363: "7",
            803050: "4",
            839934: "2",
            941617: "5",
            941651: "13",
            941672: "12",
            1356866: "20",
            1356899: "6",
            1504240: "16",
            1540214: "11",
            1776975: "8",
            1810722: "15",
            3522286: "19",
            15269345: "1|2|3|4",
            42076436: "5|6|7|8",
        },
    }, "Parsed a normal series"


def test__parse_series_missing_numbering() -> None:
    r = ElementTree.parse("t/data/series/397249.xml")
    assert _parse_series(r) == {
        "Series": "British Library Tales of the Weird",
        "Count": "55",
        "Entries": [],
        "Works": {
            955499: "49",
            3150114: "42",
            3866909: "55",
            3911685: "46",
            3911701: "26",
            6329020: "51",
            43692416: "7",
            63653740: "1",
            64372672: "2",
            64423217: "3",
            65780685: "4",
            65800327: "5",
            67992174: "6",
            68621783: "8",
            70220678: "9",
            70259906: "10",
            72400938: "12",
            72400941: "13",
            72400943: "11",
            75775297: "15",
            75775298: "14",
            75775300: "18",
            75775305: "16",
            85156587: "17",
            85721990: "19",
            85721994: "21",
            85721995: "20",
            89074937: "23",
            89074978: "22",
            91441919: "24",
            91441920: "25",
            91532910: "27",
            94024709: "29",
            94024718: "31",
            94918950: "30",
            96680809: "33",
            96680810: "32",
            99031887: "34",
            99229101: "35",
            145254345: "37",
            145254410: "39",
            175476467: "38",
            175476972: "36",
            197536168: "43",
            201785067: "40",
            203380149: "41",
            208897246: "44",
            211578145: "45",
            216464290: "47",
            217372902: "48",
            220295758: "50",
            222703814: "28",
            222704898: "52",
            222704989: "53",
            222705066: "54",
        },
    }, "Parsed a series without entry numbers"


def test__get_entry() -> None:
    assert _get_entry("1") == 1
    assert _get_entry("3") == 3
    assert _get_entry("1.1") is None
    assert _get_entry("1 of 2") == 1


def test__parse_entries() -> None:
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
