# vim: ts=4 : sw=4 : et

from pathlib import Path

import pytest

from reading.wordcounts import (
    Metadata,
    _as_text,
    _count_words,
    _ignore_item,
    _read_metadata,
    get_ebooks,
)


################################################################################


def test__ignore_item(tmp_path: Path) -> None:
    p = tmp_path / "item.mobi"
    p.touch()
    assert not _ignore_item(p), "Interesting path"

    p = tmp_path / ".hidden.mobi"
    p.touch()
    assert _ignore_item(p), "Hidden files are ignored"

    p = tmp_path / "dir"
    p.mkdir()
    assert _ignore_item(p), "Directories are ignored"

    p = tmp_path / "My Clippings.txt"
    p.touch()
    assert _ignore_item(p), "Ignored filename"

    p = tmp_path / "item.kfx"
    p.touch()
    assert _ignore_item(p), "Ignored extension"


def _populate_dir(basedir: Path, dirname: str, files: list[str]) -> None:
    directory = basedir / dirname

    directory.mkdir(exist_ok=True)

    for fname in files:
        (directory / fname).touch()


def test_get_ebooks(tmp_path: Path) -> None:
    # create the directories
    _populate_dir(tmp_path, "articles", ["art1.azw3", "art2.txt", "art3.pdf"])
    _populate_dir(tmp_path, ".", ["article4.azw3", "item.kfx"])
    _populate_dir(tmp_path, "books", ["novel1.azw3", "novel2.txt", "novel3.mobi"])
    _populate_dir(tmp_path, "non-fiction", ["essay1.azw3", "essay2.txt"])
    _populate_dir(tmp_path, "short-stories", ["stories1.azw3", ".hidden"])

    assert [(c, str(p.relative_to(tmp_path)), n) for c, p, n in sorted(get_ebooks(tmp_path))] == [
        ("articles", "article4.azw3", "articles/article4.azw3"),
        ("articles", "articles/art1.azw3", "articles/art1.azw3"),
        ("articles", "articles/art2.txt", "articles/art2.txt"),
        ("articles", "articles/art3.pdf", "articles/art3.pdf"),
        ("non-fiction", "non-fiction/essay1.azw3", "non-fiction/essay1.azw3"),
        ("non-fiction", "non-fiction/essay2.txt", "non-fiction/essay2.txt"),
        ("novels", "books/novel1.azw3", "novels/novel1.azw3"),
        ("novels", "books/novel2.txt", "novels/novel2.txt"),
        ("novels", "books/novel3.mobi", "novels/novel3.mobi"),
        ("short-stories", "short-stories/stories1.azw3", "short-stories/stories1.azw3"),
    ]


################################################################################

ebook_paths = list(Path("t/data/ebooks").iterdir())
ebook_names = [path.name for path in Path("t/data/ebooks").iterdir()]


@pytest.mark.slow
@pytest.mark.parametrize("path", ebook_paths, ids=ebook_names)
def test__as_text(path: Path) -> None:
    assert _as_text(path) == path.with_suffix(".txt").read_bytes()


def test_missing_ebook_convert(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PATH", "/no/such/path")
    path = Path("t/data/ebooks/supernatural.mobi")
    assert _as_text(path) is None, "Missing ebook-convert command"


def test_ebook_invalid(tmp_path: Path) -> None:
    path = tmp_path / "blah.mobi"
    path.write_bytes(b"blah")
    assert _as_text(path) is None, "Error converting the ebook"


def test__count_words() -> None:
    assert _count_words(None) is None, "Works when there was a problem converting"
    assert _count_words("") == 0
    assert _count_words("word") == 1
    assert _count_words("two words") == 2
    assert _count_words(b"two words") == 2, "Works with bytestrings too"


################################################################################


def test__read_metadata() -> None:
    path = Path("t/data/ebooks/supernatural.mobi")
    assert _read_metadata(path) == {
        "Authors": ["H. P. Lovecraft"],
        "Languages": ["en"],
        "Title": "Supernatural Horror in Literature",
    }

    path = Path("t/data/ebooks/pg4559.mobi")
    assert _read_metadata(path) == {
        "Authors": ["Jules Renard"],
        "Languages": ["fr"],
        "Title": "Poil de Carotte",
    }

    path = Path("t/data/ebooks/pg6838.mobi")
    assert _read_metadata(path) == {
        "Authors": ["Victor Hugo"],
        "Languages": ["fr"],
        "Title": "Le Dernier Jour d'un Condamné",
    }, "Metadata with diacritical marks"


def test_metadata() -> None:
    m = Metadata(
        {
            "Authors": ["H. P. Lovecraft"],
            "Languages": ["en"],
            "Title": "Supernatural Horror in Literature",
        }
    )
    assert m.author == "H. P. Lovecraft"
    assert m.language == "en"
    assert m.title == "Supernatural Horror in Literature"

    m = Metadata(
        {
            "Authors": ["H. P. Lovecraft"],
            "Languages": [],
            "Title": "Supernatural Horror in Literature",
        }
    )
    assert m.language == "en", "Default language is 'en'"

    m = Metadata(
        {
            "Authors": ["Victor Hugo"],
            "Languages": ["fr"],
            "Title": "Le Dernier Jour d'un Condamné",
        }
    )
    assert m.author == "Victor Hugo"
    assert m.language == "fr"
    assert m.title == "Le Dernier Jour d'un Condamné"
