# vim: ts=4 : sw=4 : et

from pathlib import Path

import pytest

from reading.wordcounts import _ignore_item, get_ebooks, _as_text, _count_words


def test__ignore_item(tmp_path):
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


def _populate_dir(basedir, dirname, files):
    try:
        (basedir / dirname).mkdir()
    except FileExistsError:
        pass

    for fname in files:
        (basedir / dirname / fname).touch()


def test_get_ebooks(tmp_path):
    # create the directories
    _populate_dir(
        tmp_path, "articles", ["art1.azw3", "art2.txt", "art3.pdf"]
    )
    _populate_dir(tmp_path, ".", ["article4.azw3", "item.kfx"])
    _populate_dir(tmp_path, "books", ["novel1.azw3", "novel2.txt", "novel3.mobi"])
    _populate_dir(tmp_path, "non-fiction", ["essay1.azw3", "essay2.txt"])
    _populate_dir(tmp_path, "short-stories", ["stories1.azw3", ".hidden"])

    assert [
        (c, str(p.relative_to(tmp_path)), n) for c, p, n in sorted(get_ebooks(tmp_path))
    ] == [
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


@pytest.mark.slow
def test__as_text():
    for path in [
        Path("t/data/ebooks/supernatural.mobi"),
        Path("t/data/ebooks/pg4559.mobi"),
        Path("t/data/ebooks/pg6838.mobi"),
    ]:
        assert _as_text(path) == path.with_suffix(".txt").read_bytes()


def idfn(val):
    return val.name


@pytest.mark.slow
@pytest.mark.parametrize("path", list(Path("t/data/ebooks").iterdir()), ids=idfn)
def test_wordcount(path):
    from reading.wordcounts import wordcount
    new_words = _count_words(_as_text(path))
    old_words = wordcount(path)

    assert abs(new_words - old_words) < 100


def test__count_words():
    assert _count_words(None) is None, "Works when there was a problem converting"
    assert _count_words("") == 0
    assert _count_words("word") == 1
    assert _count_words("two words") == 2
    assert _count_words(b"two words") == 2, "Works with bytestrings too"
