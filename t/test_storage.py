# vim: ts=4 : sw=4 : et

from pathlib import Path

import pandas as pd
import pytest

from reading.collection import Collection
from reading.storage import Store, load_df, save_df


def test_load_df() -> None:
    df = load_df("authors")
    assert df is not None, "Loaded an existing dataframe"

    df = load_df("authors", fname="/does/not/exist")
    assert df.empty, "Loaded a dataframe from a missing file"


def test_save_df(tmp_path: Path) -> None:
    df = Collection.from_dir("t/data/2019-12-04", fixes=False, metadata=False).df

    # pick out a few books
    df = df[df.AuthorId == 9121]

    sorted_csv = tmp_path / "ebooks.csv"
    save_df("ebooks", df, sorted_csv)
    assert (
        sorted_csv.read_text()
        == """\
BookId,Author,Title,Category,Language,Words,Added
38290,James Fenimore Cooper,The Pioneers,novels,,,2017-02-27
246245,James Fenimore Cooper,The Deerslayer,novels,en,,2016-11-08
347245,James Fenimore Cooper,The Pathfinder,novels,en,,2016-11-08
621017,James Fenimore Cooper,The Prairie,novels,,,2016-11-08
1041744,James Fenimore Cooper,The Last of the Mohicans,novels,,,2017-02-16
"""
    ), "Wrote a csv of only some columns"

    shuffled_df = df[sorted(df.columns)].sample(frac=1)
    shuffled_csv = tmp_path / "shuffled.csv"
    save_df("ebooks", shuffled_df, shuffled_csv)
    assert (
        shuffled_csv.read_text()
        == """\
BookId,Author,Title,Category,Language,Words,Added
38290,James Fenimore Cooper,The Pioneers,novels,,,2017-02-27
246245,James Fenimore Cooper,The Deerslayer,novels,en,,2016-11-08
347245,James Fenimore Cooper,The Pathfinder,novels,en,,2016-11-08
621017,James Fenimore Cooper,The Prairie,novels,,,2016-11-08
1041744,James Fenimore Cooper,The Last of the Mohicans,novels,,,2017-02-16
"""
    ), "CSV is ordered even if the df isn't"


################################################################################


def test_store() -> None:
    """Basic functionality."""
    store = Store()
    assert store
    assert store.directory == Path("data"), "The default directory is sensible"
    assert str(store) == "Store(directory=data)", "It stringifies nicely"


def test_empty_store(tmp_path: Path) -> None:
    """When the store is empty."""
    store = Store(tmp_path)

    assert isinstance(store.goodreads, pd.DataFrame), "Got a dataframe"
    assert store.goodreads.empty, "There was no data on disk so it created one"

    # the metadata stores are a bit more complicated
    assert isinstance(store.gr_metadata, pd.DataFrame), "Got a dataframe"
    assert store.gr_metadata.empty, "There was no data on disk so it created one"


def test_existing_store() -> None:
    """When there is already data in the store."""
    store = Store("t/data/2019-12-04")

    ebooks = store.ebooks
    assert isinstance(ebooks, pd.DataFrame), "Got a dataframe"
    assert "novels/pg13947.mobi" in ebooks.index, "There are books in the dataframe"

    # the metadata stores are a bit more complicated
    ebook_metadata = store.ebook_metadata
    assert isinstance(ebook_metadata, pd.DataFrame), "Got a dataframe"
    assert "non-fiction/pg14154.mobi" in ebook_metadata.index, "There are books in the dataframe"


def test_store_overwrite() -> None:
    store = Store("t/data/2019-12-04")

    assert not store.ebooks.empty
    store.ebooks = pd.DataFrame()
    assert store.ebooks.empty

    assert not store.ebook_metadata.empty
    store.ebook_metadata = pd.DataFrame()
    assert store.ebook_metadata.empty


def test_store_mistakes(tmp_path: Path) -> None:
    """Mistakes should be obvious: cannot fetch an unrecognised table."""
    store = Store(tmp_path)

    with pytest.raises(AttributeError):
        table = store.blabla  # type: ignore[attr-defined] # pylint: disable=no-member
        assert not table


def _is_empty(directory: Path) -> bool:
    return not any(directory.iterdir())


def test_store_save_noop(tmp_path: Path) -> None:
    """Only changed tables are saved (for now)."""
    store = Store()
    assert _is_empty(tmp_path), "Directory is empty"

    store.save(tmp_path)

    assert _is_empty(tmp_path), "No tables were changed so none were saved"


def test_store_save_changed(tmp_path: Path) -> None:
    """Only changed tables are saved (for now)."""
    store = Store()
    empty = Store(tmp_path)

    store.ebooks = empty.ebooks
    assert store.ebooks.empty, "The ebooks table is now empty"

    store.save(tmp_path)

    assert [p.stem for p in tmp_path.iterdir()] == ["ebooks"], "The changed table was saved"

    store = Store(tmp_path)
    assert store.ebooks.empty, "On reload the table is still empty"
