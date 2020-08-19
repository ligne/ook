# vim: ts=4 : sw=4 : et

import textwrap
import yaml

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

from reading.collection import NewCollection as Collection, _process_fixes


################################################################################

def test_collection():
    """General tests."""
    c = Collection.from_dir(None)
    assert c, "Created an empty collection"
    assert c.merge is False, "No merge by default"
    assert c.dedup is False, "No dedup by default"
    assert (
        repr(c) == "NewCollection(_df=[0 books], merge=False, dedup=False)"
    ), "Legible __repr__ for an empty collection"

    c = Collection.from_dir("t/data/2019-12-04/")
    assert c, "Created a collection from a directory"
    assert (
        repr(c) == "NewCollection(_df=[160 books], merge=False, dedup=False)"
    ), "Legible __repr__ for a collection with books"

    c = Collection.from_dir(None, merge=True)
    assert c.merge is True, "Enabled merging"
    assert c.dedup is False, "No dedup by default"

    c = Collection.from_dir(None, merge=True, dedup=True)
    assert c.merge is True, "Enabled merging"
    assert c.dedup is True, "Enabled dedup"


def test_kindle_books():
    """Tests specific to ebooks."""
    c = Collection.from_dir("t/data/2019-12-04/")
    df = c.all
    df = df[df.Shelf == "kindle"]

    assert set(df.Binding) == {"ebook"}, "ebook binding is always 'ebook'"
    assert set(df.Borrowed) == {False}, "ebooks are never borrowed"
    assert set(df.Shelf) == {"kindle"}, "ebook shelf is always 'kindle'"

    b = df.loc["non-fiction/pg14154.mobi"]  # A Tale of Terror
    assert str(b.Added.date()) == "2013-02-06", "Added date is sensible"


def test_collection_columns():
    """Test the columns are present and correct."""
    df = Collection.from_dir("t/data/2019-12-04")._df

    assert list(df.columns) == [
        "Author",
        "AuthorId",
        "Title",
        "Work",
        "Shelf",
        "Category",
        "Scheduled",
        "Borrowed",
        "Series",
        "SeriesId",
        "Entry",
        "Binding",
        "Published",
        "Language",
        "Pages",
        "Added",
        "Started",
        "Read",
        "Rating",
        "AvgRating",
        "Words",
        # "Gender",
        # "Nationality",
        "_Mask",  # FIXME
    ]

    b = df.loc[2366570]  # Les Chouans

    # timestamp columns are ok
    assert str(b.Added.date()) == "2016-04-18"
    assert str(b.Started.date()) == "2016-09-08"
    assert str(b.Read.date()) == "2016-11-06"
    assert b.Published == 1829  # pandas can't do very old dates...

    b = df.loc[3071647]  # La faute de l'abbé Mouret
    assert str(b.Scheduled.date()) == "2020-01-01", "Scheduled column is a timestamp"

    b = df.loc[28595808]  # The McCabe Reader
    # missing publication year
    assert np.isnan(b.Published)

    df = Collection.from_dir("t/data/2019-12-04")._df
    assert set(df.Category) == {
        "articles",
        "novels",
        "short-stories",
        "non-fiction",
        "graphic",
        np.nan,
    }


def test_reset():
    """Test the reset() method."""
    c1 = Collection.from_dir("t/data/2019-12-04")
    c2 = Collection.from_dir("t/data/2019-12-04")

    assert_frame_equal(c1.df, c2.df)  # Identical dataframes are the same"

    c2.shelves(["library"])
    assert not c1.df.equals(c2.df), "Changed dataframe is different"

    c2.reset()
    assert_frame_equal(c1.df, c2.df)  # Reset dataframe is the same again


################################################################################

# fixes/metadata

def test__process_fixes():
    """Test the fix munging function."""
    assert not _process_fixes({}), "No fixes to apply"

    fixes = yaml.safe_load("""
        general:
          - BookId: 20636970  # La Curée
            Read: 2018-02-09
          - BookId: 3263729  # The Mabinogion
            Started: 2019-08-06
        columns:
          Category:
            non-fiction:
              - 1777481  # Culture and Society in France 1789-1848
              - 3110594  # Zola: Le saut dans les étoiles
          Language:
            fr:
              - 140785  # Maigret Hésite
              - 770786  # Le Horla et autres nouvelles
              - 816920  # Nana
            en:
              - 58614  # A Beleaguered City and Other Stories
    """)

    assert _process_fixes(fixes).to_csv() == textwrap.dedent("""\
        ,Category,Language,Read,Started
        20636970,,,2018-02-09,
        3263729,,,,2019-08-06
        1777481,non-fiction,,,
        3110594,non-fiction,,,
        140785,,fr,,
        770786,,fr,,
        816920,,fr,,
        58614,,en,,
    """), "Rearranged some fixes"

    general_only = {k: v for k, v in fixes.items() if k == "general"}
    assert _process_fixes(general_only).to_csv() == textwrap.dedent("""\
        ,Read,Started
        20636970,2018-02-09,
        3263729,,2019-08-06
    """), "Only general fixes"

    columnar_only = {k: v for k, v in fixes.items() if k == "columns"}
    assert _process_fixes(columnar_only).to_csv() == textwrap.dedent("""\
        ,Category,Language
        1777481,non-fiction,
        3110594,non-fiction,
        140785,,fr
        770786,,fr
        816920,,fr
        58614,,en
    """), "Only columnar fixes"


################################################################################

# access

def test_df():
    """Test the .df property."""
    c = Collection.from_dir("t/data/2019-12-04/")

    assert c.df is not None

    # test with merging and dedup


def test_all():
    """Test the .all property."""
    c = Collection.from_dir("t/data/2019-12-04/")

    assert_frame_equal(c.df, c.all)  # .df and .all are the same when no filters applied

    df = c.all.copy()
    assert_frame_equal(df, c.shelves(["read"]).all)  # .all is not affected by filters


def test_read():
    """Test the .read property."""
    c = Collection.from_dir("t/data/2019-12-04/")

    df = c.read

    assert set(df.Shelf) == {"read", "currently-reading"}, "Only expected shelves"

    assert 10374 in df.index, "Read book is there"
    assert 38290 not in df.index, "Unread book is not"
    assert 38290 in c.all.index, "Unread book is still in the collection however"

    all_read = c.read.copy()  # copy to be safe

    assert_frame_equal(
        c.shelves(["library"]).read, all_read
    )  # Same result even with a filtered frame


################################################################################

def test_filter_shelves():
    """Test the shelves() method."""
    c = Collection.from_dir("t/data/2019-12-04")
    c2 = Collection.from_dir("t/data/2019-12-04")

    assert_frame_equal(c.shelves().df, c2.df)  # no argument makes it a no-op

    assert set(c.shelves(["library"]).df.Shelf) == {"library"}, "Only the selected shelf"

    c.reset()

    c.shelves(exclude=["library"])
    assert "library" not in set(c.df.Shelf), "Not the excluded shelf"
    assert "kindle" in set(c.df.Shelf), "Does include others"

    c = Collection.from_dir("t/data/2019-12-04")
    df = pd.concat([
        Collection.from_dir("t/data/2019-12-04").shelves(exclude=["library"]).df,
        Collection.from_dir("t/data/2019-12-04").shelves(include=["library"]).df,
    ])
    assert_frame_equal(df, c.df, check_like=True)  # A ∪ ¬A = U, though the rows get mixed up


def test_filter_languages():
    """Test the language() method."""
    c = Collection.from_dir("t/data/2019-12-04")
    c2 = Collection.from_dir("t/data/2019-12-04")

    assert_frame_equal(c.languages().df, c2.df)  # no argument makes it a no-op

    assert set(c.languages(["fr"]).df.Language) == {"fr"}, "Only the selected language"

    c.reset()

    c.languages(exclude=["fr"])
    assert "fr" not in set(c.df.Language), "Not the excluded language"
    assert "en" in set(c.df.Language), "Does include others"

    c = Collection.from_dir("t/data/2019-12-04")
    df = pd.concat([
        Collection.from_dir("t/data/2019-12-04").languages(exclude=["fr"]).df,
        Collection.from_dir("t/data/2019-12-04").languages(include=["fr"]).df,
    ])
    assert_frame_equal(df, c.df, check_like=True)  # A ∪ ¬A = U, though the rows get mixed up


def test_filter_categories():
    """Test the categories() metod."""
    c = Collection.from_dir("t/data/2019-12-04")
    c2 = Collection.from_dir("t/data/2019-12-04")

    assert_frame_equal(c.categories().df, c2.df)  # no argument makes it a no-op

    assert set(c.categories(["novels"]).df.Category) == {"novels"}, "Only the selected language"

    c.reset()

    c.categories(exclude=["novels"])
    assert "novels" not in set(c.df.Category), "Not the excluded category"
    assert "articles" in set(c.df.Category), "Does include others"

    c = Collection.from_dir("t/data/2019-12-04")
    df = pd.concat([
        Collection.from_dir("t/data/2019-12-04").categories(exclude=["novels"]).df,
        Collection.from_dir("t/data/2019-12-04").categories(include=["novels"]).df,
    ])
    assert_frame_equal(df, c.df, check_like=True)  # A ∪ ¬A = U, though the rows get mixed up


def test_filter_borrowed():
    """Test the borrowed() method."""
    c = Collection.from_dir("t/data/2019-12-04")
    assert set(c.borrowed().df.Borrowed) == {True, False}

    c = Collection.from_dir("t/data/2019-12-04")
    assert set(c.borrowed(True).df.Borrowed) == {True}

    c = Collection.from_dir("t/data/2019-12-04")
    assert set(c.borrowed(False).df.Borrowed) == {False}


def test_chaining():
    """Test that filters chain correctly."""
    c = Collection.from_dir("t/data/2019-12-04")
    c.shelves(["pending"]).borrowed(True).languages(["fr"])

    assert_frame_equal(
        c.df, c.all[(c.all.Shelf == "pending") & c.all.Borrowed & (c.all.Language == "fr")]
    )

    c = Collection.from_dir("t/data/2019-12-04")
    c.shelves(["pending"]).categories(["graphic"]).languages(exclude=["fr"]).borrowed(False)

    assert_frame_equal(
        c.df,
        c.all[
            (c.all.Shelf == "pending")
            & (c.all.Category == "graphic")
            & (c.all.Language == "fr")
            & ~c.all.Borrowed
        ],
    )
