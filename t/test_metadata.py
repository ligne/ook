# vim: ts=4 : sw=4 : et

from __future__ import annotations

import json
from pathlib import Path
import re

import pytest

from reading.config import Config
from reading.metadata import FullExit, SaveExit, _list_book_choices, _read_choice, confirm_author
from reading.storage import Store
from reading.wikidata import Entity


def _colour_to_string(colour: str) -> str:
    styles = ["RESET", "BOLD", "FAINT", "ITALIC", "REVERSE"]
    codes = ["BLACK", "RED", "GREEN", "YELLOW", "BLUE", "MAGENTA", "CYAN", "WHITE"]
    effects = {
        "3": "",  # foreground
        "4": "B",  # background
        "9": "BRIGHT",
    }

    if len(colour) == 1:
        return styles[int(colour)]

    effect, code = list(colour)
    return effects[effect] + codes[int(code)]


def _decode_colourspec(match: re.Match[str]) -> str:
    return "<" + ";".join([_colour_to_string(colour) for colour in match.group(1).split(";")]) + ">"


def decode_colour(string: str) -> str:
    return re.sub("\033" + r"\[([0-9;]*)m", _decode_colourspec, string)


def test_decode_colour() -> None:
    assert decode_colour("") == ""
    assert decode_colour("blah") == "blah"
    assert decode_colour("\033[0m") == "<RESET>"
    assert decode_colour("blah\033[32m") == "blah<GREEN>"
    assert decode_colour("blah\033[31mbloh\033[34;42m") == "blah<RED>bloh<BLUE;BGREEN>"
    assert decode_colour("\033[94;42m text") == "<BRIGHTBLUE;BGREEN> text"


#################################################################################


def test__list_book_choices() -> None:
    # nothing
    assert _list_book_choices([], set(), set()) == ""

    # books from goodreads title search
    assert (
        decode_colour(
            _list_book_choices(
                [
                    {
                        "Ratings": "31583",
                        "Published": "1853",
                        "BookId": "182381",
                        "Work": "1016559",
                        "Author": "Elizabeth Gaskell",
                        "AuthorId": "1413437",
                        "Title": "Cranford",
                    },
                    {
                        "Ratings": "1515",
                        "Published": "1859",
                        "BookId": "2141817",
                        "Work": "21949576",
                        "Author": "Elizabeth Gaskell",
                        "AuthorId": "1413437",
                        "Title": "The Cranford Chronicles",
                    },
                    {
                        "Ratings": "74",
                        "Published": "2009",
                        "BookId": "7329542",
                        "Work": "8965360",
                        "Author": "Elizabeth Gaskell",
                        "AuthorId": "1413437",
                        "Title": "Return to Cranford: Cranford and other stories",
                    },
                    {
                        "Ratings": "10",
                        "Published": "2000",
                        "BookId": "732416",
                        "Work": "718606",
                        "Author": "J.Y.K. Kerr",
                        "AuthorId": "1215308",
                        "Title": "Cranford",
                    },
                    {
                        "Ratings": "428",
                        "Published": "1864",
                        "BookId": "222401",
                        "Work": "215385",
                        "Author": "Elizabeth Gaskell",
                        "AuthorId": "1413437",
                        "Title": "Cranford/Cousin Phillis",
                    },
                ],
                set(),
                set(),
            )
        )
        == """\
<BOLD> 1.<RESET> Cranford<RESET>
      Elizabeth Gaskell<RESET>
      Published: 1853
      Ratings: 31583
      https://www.goodreads.com/book/show/182381
      https://www.goodreads.com/author/show/1413437
 2. The Cranford Chronicles<RESET>
      Elizabeth Gaskell<RESET>
      Published: 1859
      Ratings: 1515
      https://www.goodreads.com/book/show/2141817
      https://www.goodreads.com/author/show/1413437
 3. Return to Cranford: Cranford and other stories<RESET>
      Elizabeth Gaskell<RESET>
      Published: 2009
      Ratings: 74
      https://www.goodreads.com/book/show/7329542
      https://www.goodreads.com/author/show/1413437
 4. Cranford<RESET>
      J.Y.K. Kerr<RESET>
      Published: 2000
      Ratings: 10
      https://www.goodreads.com/book/show/732416
      https://www.goodreads.com/author/show/1215308
 5. Cranford/Cousin Phillis<RESET>
      Elizabeth Gaskell<RESET>
      Published: 1864
      Ratings: 428
      https://www.goodreads.com/book/show/222401
      https://www.goodreads.com/author/show/1413437
"""
    )

    # it's both an author and a work that i have already.
    results = [
        {
            "Work": "3298883",
            "AuthorId": "5144",
            "BookId": "7588",
            "Ratings": "109451",
            "Published": "1916",
            "Author": "James Joyce",
            "Title": "A Portrait of the Artist as a Young Man",
        },
        {
            "Work": "47198830",
            "AuthorId": "5144",
            "BookId": "23296",
            "Ratings": "5733",
            "Published": "1914",
            "Author": "James Joyce",
            "Title": "A Portrait of the Artist as a Young Man / Dubliners",
        },
        {
            "Work": "7427316",
            "AuthorId": "5144",
            "BookId": "580717",
            "Ratings": "113",
            "Published": "1992",
            "Author": "James Joyce",
            "Title": "Dubliners/A Portrait of the Artist As a Young Man/Chamber Music",
        },
        {
            "Work": "10692",
            "AuthorId": "5677665",
            "BookId": "7593",
            "Ratings": "12",
            "Published": "1964",
            "Author": "Valerie Zimbarro",
            "Title": "A Portrait of the Artist as a Young Man, Notes",
        },
    ]
    assert (
        decode_colour(_list_book_choices(results, author_ids={5144}, work_ids={3298883}))
        == """\
<BOLD> 1.<RESET><GREEN> A Portrait of the Artist as a Young Man<RESET><YELLOW>
      James Joyce<RESET>
      Published: 1916
      Ratings: 109451
      https://www.goodreads.com/book/show/7588
      https://www.goodreads.com/author/show/5144
 2. A Portrait of the Artist as a Young Man / Dubliners<RESET><YELLOW>
      James Joyce<RESET>
      Published: 1914
      Ratings: 5733
      https://www.goodreads.com/book/show/23296
      https://www.goodreads.com/author/show/5144
 3. Dubliners/A Portrait of the Artist As a Young Man/Chamber Music<RESET><YELLOW>
      James Joyce<RESET>
      Published: 1992
      Ratings: 113
      https://www.goodreads.com/book/show/580717
      https://www.goodreads.com/author/show/5144
 4. A Portrait of the Artist as a Young Man, Notes<RESET>
      Valerie Zimbarro<RESET>
      Published: 1964
      Ratings: 12
      https://www.goodreads.com/book/show/7593
      https://www.goodreads.com/author/show/5677665
"""
    )

    # known author, but new book
    results = [
        {
            "Work": "3298883",
            "AuthorId": "5144",
            "BookId": "7588",
            "Ratings": "109451",
            "Published": "1916",
            "Author": "James Joyce",
            "Title": "A Portrait of the Artist as a Young Man",
        },
        {
            "Work": "47198830",
            "AuthorId": "5144",
            "BookId": "23296",
            "Ratings": "5733",
            "Published": "1914",
            "Author": "James Joyce",
            "Title": "A Portrait of the Artist as a Young Man / Dubliners",
        },
        {
            "Work": "7427316",
            "AuthorId": "5144",
            "BookId": "580717",
            "Ratings": "113",
            "Published": "1992",
            "Author": "James Joyce",
            "Title": "Dubliners/A Portrait of the Artist As a Young Man/Chamber Music",
        },
        {
            "Work": "10692",
            "AuthorId": "5677665",
            "BookId": "7593",
            "Ratings": "12",
            "Published": "1964",
            "Author": "Valerie Zimbarro",
            "Title": "A Portrait of the Artist as a Young Man, Notes",
        },
    ]
    assert (
        decode_colour(_list_book_choices(results, author_ids={5144}, work_ids=set()))
        == """\
<BOLD> 1.<RESET> A Portrait of the Artist as a Young Man<RESET><YELLOW>
      James Joyce<RESET>
      Published: 1916
      Ratings: 109451
      https://www.goodreads.com/book/show/7588
      https://www.goodreads.com/author/show/5144
 2. A Portrait of the Artist as a Young Man / Dubliners<RESET><YELLOW>
      James Joyce<RESET>
      Published: 1914
      Ratings: 5733
      https://www.goodreads.com/book/show/23296
      https://www.goodreads.com/author/show/5144
 3. Dubliners/A Portrait of the Artist As a Young Man/Chamber Music<RESET><YELLOW>
      James Joyce<RESET>
      Published: 1992
      Ratings: 113
      https://www.goodreads.com/book/show/580717
      https://www.goodreads.com/author/show/5144
 4. A Portrait of the Artist as a Young Man, Notes<RESET>
      Valerie Zimbarro<RESET>
      Published: 1964
      Ratings: 12
      https://www.goodreads.com/book/show/7593
      https://www.goodreads.com/author/show/5677665
"""
    )


# helper to raise from inside a lambda
def _raise(exception):
    raise exception


def test__read_choice(monkeypatch: pytest.MonkeyPatch) -> None:
    length = 3

    monkeypatch.setattr("builtins.input", lambda prompt: "1")
    assert _read_choice(length) == "1", "Selected an index"

    monkeypatch.setattr("builtins.input", lambda prompt: "")
    assert _read_choice(length) == "1", "Default index is 1"

    monkeypatch.setattr("builtins.input", lambda prompt: "q")
    with pytest.raises(SaveExit):
        assert _read_choice(length), "Asked to save and quit"

    monkeypatch.setattr("builtins.input", lambda prompt: "Q")
    with pytest.raises(FullExit):
        assert _read_choice(length), "Asked to save and quit"

    monkeypatch.setattr("builtins.input", lambda prompt: "s")
    assert not _read_choice(length), "Skip to the next"

    monkeypatch.setattr("builtins.input", lambda prompt: _raise(EOFError))
    with pytest.raises(SaveExit):
        assert _read_choice(length), "Ctrl-D saves and exits"

    monkeypatch.setattr("builtins.input", lambda prompt: _raise(KeyboardInterrupt))
    with pytest.raises(FullExit):
        assert _read_choice(length), "Ctrl-C exits without saving"

    inputs = (x for x in ["7", "t", "2"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))
    assert _read_choice(length) == "2", "Invalid option"

    inputs = (x for x in ["?", "1"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))
    assert _read_choice(length) == "1", "Request the help message"


def test__read_choice_output(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    length = 3

    monkeypatch.setattr("builtins.input", lambda prompt: "1")
    _read_choice(length)
    output = capsys.readouterr()
    assert output.out == ""

    inputs = (x for x in ["?", "1"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))
    _read_choice(length)
    output = capsys.readouterr()
    assert (
        decode_colour(output.out)
        == """
<BRIGHTRED>1-3 - select

s - skip to the next author
q - save and exit
Q - exit without saving
? - print help<RESET>
""".lstrip()
    )


################################################################################


def _load_json(qid: str):
    with open(f"t/data/wikidata/entities/{qid}.json") as fh:
        return json.load(fh)["entities"][qid]


def test_confirm_author_reject(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr("builtins.input", lambda prompt: "n")

    entity = Entity(_load_json("Q12807"))
    author = confirm_author(entity)
    output = capsys.readouterr()
    assert (
        decode_colour(output.out)
        == """
<GREEN>Umberto Eco: male, it<RESET>

"""
    )
    assert author is None


def test_confirm_author_accept(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("builtins.input", lambda prompt: "y")

    entity = Entity(_load_json("Q12807"))
    author = confirm_author(entity)
    assert author == {
        "QID": "Q12807",
        "Author": "Umberto Eco",
        "Gender": "male",
        "Nationality": "it",
        "Description": "Italian semiotician, essayist, philosopher, literary critic, and novelist",
    }


def test_confirm_author_default_accepts(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("builtins.input", lambda prompt: "")

    entity = Entity(_load_json("Q12807"))
    author = confirm_author(entity)
    assert author["Nationality"] == "it"
