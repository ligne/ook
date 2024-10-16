# vim: ts=4 : sw=4 : et

from __future__ import annotations

import math
import textwrap

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
import pytest
import yaml

from reading.collection import Collection, _process_fixes, read_authorids, read_nationalities
from reading.config import Config
from reading.storage import Store


################################################################################


def test_read_authorids() -> None:
    c = Collection.from_dir("t/data/2019-12-04")

    assert read_authorids(c) == {
        1654,
        3354,
        4750,
        4785,
        7628,
        9343,
        228089,
        874602,
        2778055,
        5807106,
    }

    assert 2778055 in read_authorids(c), "Author in currently-reading is included"


def test_read_nationalities() -> None:
    c = Collection.from_dir("t/data/2019-12-04")

    assert read_nationalities(c) == {"fr", "us", "jp", "gb"}


################################################################################


def test_collection() -> None:
    """General tests."""
    c = Collection.from_dir("/does/not/exist")
    assert c, "Created an empty collection"
    assert c.merge is False, "No merge by default"
    assert c.dedup is False, "No dedup by default"
    assert (
        repr(c) == "Collection(_df=[0 books], merge=False, dedup=False)"
    ), "Legible __repr__ for an empty collection"

    c = Collection.from_dir("t/data/2019-12-04/")
    assert c, "Created a collection from a directory"
    assert (
        repr(c) == "Collection(_df=[157 books], merge=False, dedup=False)"
    ), "Legible __repr__ for a collection with books"


def test_kindle_books() -> None:
    """Tests specific to ebooks."""
    c = Collection.from_dir("t/data/2019-12-04/")
    df = c.all
    df = df[df.Shelf == "kindle"]

    assert set(df.Binding) == {"ebook"}, "ebook binding is always 'ebook'"
    assert set(df.Borrowed) == {False}, "ebooks are never borrowed"
    assert set(df.Shelf) == {"kindle"}, "ebook shelf is always 'kindle'"

    b = df.loc["non-fiction/pg14154.mobi"]  # A Tale of Terror
    assert str(b.Added.date()) == "2013-02-06", "Added date is sensible"


def test_collection_columns() -> None:
    """Test the columns are present and correct."""
    columns = [
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
        "Gender",
        "Nationality",
        "Duration",
        "Rate",
        "_Mask",  # FIXME
    ]

    c = Collection.from_dir("t/data/2019-12-04")
    assert list(c._df.columns) == columns, "All the columns are there"

    c = Collection.from_dir("t/data/2019-12-04", metadata=False)
    assert list(c._df.columns) == columns, "All the columns are still there when metadata is off"


def test_column_contents() -> None:
    """Test the columns have reasonable dtypes."""
    df = Collection.from_dir("t/data/2019-12-04")._df
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

    c = Collection.from_dir("t/data/2019-12-04", fixes=False)
    assert set(c._df.Category) == {
        "articles",
        "novels",
        "short-stories",
        "non-fiction",
        "graphic",
        np.nan,
    }


def test_reset() -> None:
    """Test the reset() method."""
    c1 = Collection.from_dir("t/data/2019-12-04")
    c2 = Collection.from_dir("t/data/2019-12-04")

    assert_frame_equal(c1.df, c2.df)  # Identical dataframes are the same

    c2.shelves("library")
    assert not c1.df.equals(c2.df), "Changed dataframe is different"

    c2.reset()
    assert_frame_equal(c1.df, c2.df)  # Reset dataframe is the same again


### Overlays ###################################################################


# transpose for more reasonable line lengths
# FIXME try to_markdown()?
def _stringify_df(df: pd.DataFrame) -> str:
    df = df.reset_index()
    stringified = df.T.to_string(float_format="{:.1f}".format, header=False)
    return f"\n{stringified}\n"


# ebook metadata


@pytest.mark.xfail()
def test_ebook_metadata_overlay() -> None:
    store = Store("t/data/overlays/")

    got = _stringify_df(_ebook_metadata_overlay(store.ebooks, store.books))  # noqa: F821
    print(got)

    assert (
        got
        == """
BookId     novels/pg155.mobi  novels/pg82.mobi
Author                   NaN      Walter Scott
AuthorId              4012.0            4345.0
Title                    NaN               NaN
Work               1044477.0         1039021.0
Series                   NaN   Waverley Novels
SeriesId                 NaN          142177.0
Entry                    NaN                 5
Published             1868.0            1819.0
Pages                  528.0             541.0
"""
    )


# author metadata


@pytest.mark.xfail()
def test_author_overlay() -> None:
    """Creating an overlay for the author metadata."""
    store = Store("t/data/overlays/")

    got = _stringify_df(
        _author_overlay(store.goodreads, store.authors, pd.DataFrame()),  # noqa: F821
    )
    print(got)

    # 819: added all the metadata
    # 2049: is completely missing
    # 6217: got some different metadata
    # 9556: some data missing
    # 2294321: some data is wrong
    assert (
        got
        == """
BookId        819    6217  9556  2294321
Gender       male  female   NaN     male
Nationality    us      no    jp       ht
"""
    )


@pytest.mark.xfail()
def test_author_overlay_fixed() -> None:
    """Creating an overlay from the author metadata, plus manual fixes."""
    store = Store("t/data/overlays/")

    author_fixes = [
        {"AuthorId": 1377, "Gender": "male"},  # missing value
        {"AuthorId": 1624, "Nationality": "us"},  # incorrect value
    ]
    author_fixes = pd.DataFrame(author_fixes).set_index("AuthorId")
    print(author_fixes)

    got = _stringify_df(
        _author_overlay(store.goodreads, store.authors, author_fixes),  # noqa: F821
    )
    print(got)

    # 2049: is included now it has some metadata
    # 9556: some data is still missing
    # 2294321: incorrect data has been fixed
    assert (
        got
        == """
BookId        819  2049    6217  9556  2294321
Gender       male  male  female   NaN     male
Nationality    us   NaN      no    jp       us
"""
    )


################################################################################

# fixes/metadata


def test__process_fixes() -> None:
    """Test the fix munging function."""
    assert _process_fixes({}).empty, "No fixes to apply"

    fixes = yaml.safe_load(
        """
      - BookId: 20636970  # La Curée
        Read: 2018-02-09
      - BookId: 3263729  # The Mabinogion
        Started: 2019-08-06
      - BookId: 1777481  # Culture and Society in France 1789-1848
        Category: non-fiction
      - BookId: 3110594  # Zola: Le saut dans les étoiles
        Category: non-fiction
      - BookId: 140785  # Maigret Hésite
        Language: fr
      - BookId: 770786  # Le Horla et autres nouvelles
        Language: fr
      - BookId: 816920  # Nana
        Language: fr
      - BookId: 58614  # A Beleaguered City and Other Stories
        Language: en
    """
    )

    fixed = _process_fixes(fixes)
    assert fixed.to_csv(columns=sorted(fixed.columns)) == textwrap.dedent(
        """\
        BookId,Category,Language,Read,Started
        20636970,,,2018-02-09,
        3263729,,,,2019-08-06
        1777481,non-fiction,,,
        3110594,non-fiction,,,
        140785,,fr,,
        770786,,fr,,
        816920,,fr,,
        58614,,en,,
    """
    ), "Rearranged some fixes"

    # Check the date columns are indeed dates
    assert pd.api.types.is_datetime64_dtype(_process_fixes(fixes).Started.dtypes)
    assert pd.api.types.is_datetime64_dtype(_process_fixes(fixes).Read.dtypes)


def test_duplicate_fixes() -> None:
    fixes = _process_fixes(
        [
            {"BookId": 20636970, "Category": "novels"},
            {"BookId": 20636970, "Pages": "567"},
        ]
    )

    assert not fixes.index.has_duplicates, "No duplicates"

    assert fixes.to_dict(orient="index") == {
        20636970: {
            "Category": np.nan,
            "Pages": "567",
        },
    }


# applying fixes


def test_fixes() -> None:
    """Test fix application."""
    c_with = Collection.from_dir("t/data/2019-12-04", metadata=False, fixes=True)
    c_wout = Collection.from_dir("t/data/2019-12-04", metadata=False, fixes=False)

    assert c_with.all.shape == c_wout.all.shape, "The shape hasn't changed"
    assert not c_with.all.equals(c_wout.all), "But they're not the same"

    # Read date has been fixed
    assert str(c_wout.all.loc[20636970].Read.date()) == "2018-03-14"
    assert str(c_with.all.loc[20636970].Read.date()) == "2018-02-09"

    # Page count has been fixed
    assert math.isnan(c_wout.all.loc[3110594].Pages)
    assert c_with.all.loc[3110594].Pages == 341

    # Category has been fixed
    assert math.isnan(c_wout.all.loc[7022275].Category)
    assert c_with.all.loc[7022275].Category == "novels"

    # Language has been fixed
    assert math.isnan(c_wout.all.loc[816920].Language)
    assert c_with.all.loc[816920].Language == "fr"

    # Fixing an ebook
    assert c_wout.all.loc["short-stories/Les_soirees_de_Medan.pdf"].Language == "en"
    assert c_with.all.loc["short-stories/Les_soirees_de_Medan.pdf"].Language == "fr"

    # FIXME also scraped.csv


def test_metadata() -> None:
    """Test metadata application."""
    c_with = Collection.from_dir("t/data/2019-12-04", fixes=False, metadata=True)
    c_wout = Collection.from_dir("t/data/2019-12-04", fixes=False, metadata=False)

    assert c_with.all.shape == c_wout.all.shape, "The shape hasn't changed"
    assert not c_with.all.equals(c_wout.all), "But they're not the same"

    assert c_with.all.Gender.notnull().any(), "At least one gender is set"
    assert c_with.all.Nationality.notnull().any(), "At least one nationality is set"

    # Metadata has been applied
    assert c_wout.all.loc["novels/b869w.mobi"].Author == "Emily, Bronte,; Brontë, Emily, 1818-1848"
    assert c_with.all.loc["novels/b869w.mobi"].Author == "Emily Brontë"


def test_fix_metadata_precedence() -> None:
    c_with = Collection.from_dir("t/data/2019-12-04", fixes=False, metadata=True)
    c_fixes = Collection.from_dir("t/data/2019-12-04", fixes=True, metadata=True)

    # Fixes take precedence over metadata
    assert c_with.all.loc["short-stories/Les_soirees_de_Medan.pdf"].Pages == 290  # from metadata
    assert c_fixes.all.loc["short-stories/Les_soirees_de_Medan.pdf"].Pages == 777  # from fixes


################################################################################

# merging guts


def test_merged() -> None:
    """General tests of the guts of the merge process."""
    c = Collection.from_dir("t/data/merging/")

    df_clean = c._df.copy()
    df = c._merged()

    assert_frame_equal(c._df, df_clean)  # _df hasn't been modified

    assert len(df) < len(df_clean), "Merged dataframe is shorter"
    assert set(df.index) < set(df_clean.index), "Remaining index values are unchanged"


def test_merged_goodreads() -> None:
    """Simple case: a goodreads book."""
    c = Collection.from_dir("t/data/merging/")
    df = c._merged()

    book = df.loc[956320]
    unmerged = c._df[c._df.Title.str.contains("Monte-Cristo")]

    assert book.Title == "Le Comte de Monte-Cristo", "Combined title has no volume number"
    assert book.Pages == sum(unmerged.Pages), "Pages is the sum"
    assert book["_Mask"], "Mask has been retained"
    assert str(book.Added.date()) == "2016-07-11"
    assert str(book.Started.date()) == "2017-02-19"
    assert str(book.Read.date()) == "2017-06-02"
    assert book.Rating == 4.5
    assert not book.Entry  # unset until i decide what to do with it


def test_merged_kindle() -> None:
    """Simple case: a kindle book."""
    c = Collection.from_dir("t/data/merging/")
    df = c._merged()

    book = df.loc["novels/pg13947.mobi"]
    unmerged = c._df[c._df.Title.str.contains("Le vicomte de Bragelonne")]

    assert book.Title == "Le vicomte de Bragelonne", "Combined title has no volume number"
    assert book.Pages == sum(unmerged.Pages), "Pages is the sum"
    assert book["_Mask"], "Mask has been retained"


def test_merged_added() -> None:
    """The earliest Added date is used."""
    c = Collection.from_dir("t/data/merging/")
    df = c._merged()

    book = df.loc[21124]
    assert str(book.Added.date()) == "2018-01-04", "Added on the earlier date"


################################################################################

# merging


def test_merge() -> None:
    """General merging tests."""
    c_un = Collection.from_dir("t/data/merging")
    assert c_un.dedup is False, "No merging by default"

    c = Collection.from_dir("t/data/merging", merge=True)
    assert c.merge is True, "Enabled merging"

    assert_frame_equal(c._df, c_un._df)  # underlying dataframes are identical


def test_merge_all() -> None:
    """Test merging."""
    c = Collection.from_dir("t/data/merging", merge=True)

    assert c.all is not None, "it didn't explode"


def test_merge_df() -> None:
    """Test merging."""
    c = Collection.from_dir("t/data/merging", merge=True)

    assert c.df is not None, "it didn't explode"

    assert 956320 in c.df.index, "Novel is there"
    c.categories("non-fiction")
    assert 21124 in c.df.index, "Non-fiction book is there"
    assert 956320 not in c.df.index, "Novel is not"


################################################################################

# deduplication


def test_dedup() -> None:
    """Test deduplication."""
    c = Collection.from_dir("t/data/2019-12-04")
    assert c.dedup is False, "No dedup by default"

    c = Collection.from_dir("t/data/2019-12-04", merge=True, dedup=True)
    assert c.merge is True, "Enabled merging"
    assert c.dedup is True, "Enabled dedup"


def test_dedup_requires_merge() -> None:
    """Deduplication currently requires merge to be enabled."""
    with pytest.raises(ValueError, match="merge"):
        Collection.from_dir("t/data/2019-12-04", merge=False, dedup=True)


### Scheduling #################################################################

# set schedule


def test_set_empty_schedule() -> None:
    """It's fine if there are no schedules configured."""
    c = Collection.from_dir("t/data/2019-12-04/")
    c.set_schedules([])
    assert c


def test_set_schedules_changed_something() -> None:
    """When there's something to do, it has an effect on the Collection."""
    c = Collection.from_dir("t/data/2019-12-04/")
    config = Config.from_file("t/data/2019-12-04/config.yml")

    assert config("scheduled")

    old_schedule = c.df.Scheduled.copy()
    c.set_schedules(config("scheduled"))
    assert (old_schedule != c.df.Scheduled).any(), "Some scheduled dates have changed"


def test_set_schedules() -> None:
    """It doesn't change the config."""
    c = Collection.from_dir("t/data/2019-12-04/")
    config = Config.from_file("t/data/2019-12-04/config.yml")

    c.set_schedules(config("scheduled"))

    clean_config = Config.from_file("t/data/2019-12-04/config.yml")
    assert config("scheduled") == clean_config("scheduled"), "The config is unchanged"


def test_schedule_without_matches() -> None:
    """It still works even if a schedule doesn't match anything."""
    # FIXME should lint for this and/or fully-read ones?
    c = Collection.from_dir("t/data/2019-12-04/")
    c.set_schedules([{"author": "blabla"}])


def test_schedule_without_selection() -> None:
    """A schedule requires something to schedule."""
    c = Collection.from_dir("t/data/2019-12-04/")
    with pytest.raises(ValueError, match="must specify at least one"):
        c.set_schedules([{"per_year": 4}])


def test_schedule_duplicated() -> None:
    c = Collection.from_dir("t/data/2019-12-04/")

    old = c.df.Scheduled.copy()

    c.set_schedules(
        [
            {"author": "Pratchett"},
            {"series": "Discworld"},
        ]
    )

    assert (old != c.df.Scheduled).any(), "The schedules have changed"


# scheduled filter


def test_scheduled_filter_in() -> None:
    c = Collection.from_dir("t/data/2019-12-04/")

    assert c.df.Scheduled.notna().any(), "Some books are scheduled"
    assert c.df.Scheduled.isna().any(), "Some books are unscheduled"
    assert c.scheduled().df.Scheduled.notna().all(), "All the books are now scheduled"


def test_scheduled_filter_out() -> None:
    c = Collection.from_dir("t/data/2019-12-04/")

    assert c.df.Scheduled.isna().any(), "Some books are unscheduled"
    assert (
        ~c.scheduled(exclude=True).df.Scheduled.notna().any()
    ), "None of the books are now scheduled"


def test_scheduled_filter_comprehensive() -> None:
    c = Collection.from_dir("t/data/2019-12-04/")

    all_books = set(c.df.index)

    scheduled_books = set(c.scheduled().df.index)
    assert scheduled_books, "There are some scheduled books"
    assert scheduled_books != all_books, "But not all of them are scheduled"

    c.reset()

    unscheduled_books = set(c.scheduled(exclude=True).df.index)
    assert unscheduled_books, "There are some unscheduled books"
    assert unscheduled_books != all_books

    assert all_books == scheduled_books | unscheduled_books, "All books are included"


# scheduled_at filter


def test_scheduled_at() -> None:
    c = Collection.from_dir("t/data/2019-12-04/")
    config = Config.from_file("t/data/2019-12-04/config.yml")

    c.set_schedules(config("scheduled"))

    assert not c.df.empty, "Got some books"
    assert c.df.Scheduled.isna().any(), "Some of the books are unscheduled"

    date = pd.Timestamp("2024-05-05")
    c.scheduled_at(date)

    assert not c.df.empty, "There are still some selected books"
    assert (c.df.Scheduled.dt.year == date.year).all(), "All the selected books are this year"
    assert (c.df.Scheduled <= date).all(), "All the selected books are scheduled before $date."

    # FIXME check the unselected books look correct


def test_scheduled_at_later() -> None:
    """Try again, this time later on in the year."""
    c = Collection.from_dir("t/data/2019-12-04/")
    config = Config.from_file("t/data/2019-12-04/config.yml")

    c.set_schedules(config("scheduled"))

    date = pd.Timestamp("2024-10-05")
    c.scheduled_at(date)

    assert not c.df.empty, "There are still some selected books"
    assert (c.df.Scheduled.dt.year == date.year).all(), "All the selected books are this year"
    assert (c.df.Scheduled <= date).all(), "All the selected books are scheduled before $date."


def test_scheduled_at_different_year() -> None:
    """It still works when the date is in a different year."""
    c = Collection.from_dir("t/data/2019-12-04/")
    config = Config.from_file("t/data/2019-12-04/config.yml")

    c.set_schedules(config("scheduled"))

    date = pd.Timestamp("2030-10-05")
    c.scheduled_at(date)

    assert not c.df.empty, "There are still some selected books"
    assert (c.df.Scheduled.dt.year == date.year).all(), "All the selected books are this year"
    assert (c.df.Scheduled <= date).all(), "All the selected books are scheduled before $date."


################################################################################

# access


def test_df() -> None:
    """Test the .df property."""
    c = Collection.from_dir("t/data/2019-12-04/")

    assert c.df is not None

    # test with merging and dedup


def test_all() -> None:
    """Test the .all property."""
    c = Collection.from_dir("t/data/2019-12-04/")

    assert_frame_equal(c.df, c.all)  # .df and .all are the same when no filters applied

    df = c.all.copy()
    assert_frame_equal(df, c.shelves("read").all)  # .all is not affected by filters


def test_read() -> None:
    """Test the .read property."""
    c = Collection.from_dir("t/data/2019-12-04/")

    df = c.read

    assert set(df.Shelf) == {"read", "currently-reading"}, "Only expected shelves"

    assert 10374 in df.index, "Read book is there"
    assert 38290 not in df.index, "Unread book is not"
    assert 38290 in c.all.index, "Unread book is still in the collection however"

    all_read = c.read.copy()  # copy to be safe

    assert_frame_equal(
        c.shelves("library").read, all_read
    )  # Same result even with a filtered frame


### Filters ####################################################################

# shelves


def test_shelves_filter_noop() -> None:
    """Using shelves() without any selection is a noop."""
    assert_frame_equal(
        Collection.from_dir("t/data/2019-12-04").shelves().df,
        Collection.from_dir("t/data/2019-12-04").df,
    )


def test_shelves_filter_in() -> None:
    """Use shelves() to filter books in."""
    c = Collection.from_dir("t/data/2019-12-04")

    c.shelves("library")

    remaining = set(c.df.Shelf)
    assert remaining == {"library"}, "Only the selected shelf"


def test_shelves_filter_out() -> None:
    """Use shelves() to filter books out."""
    c = Collection.from_dir("t/data/2019-12-04")

    c.shelves("library", exclude=True)

    remaining = set(c.df.Shelf)
    assert "library" not in remaining, "Not the excluded shelf"
    assert "kindle" in remaining, "Does include others"


def test_shelves_filter_comprehensive() -> None:
    """All the books are either included or excluded."""
    c = Collection.from_dir("t/data/2019-12-04")
    df = pd.concat(
        [
            Collection.from_dir("t/data/2019-12-04").shelves("library", exclude=True).df,
            Collection.from_dir("t/data/2019-12-04").shelves("library").df,
        ]
    )
    assert_frame_equal(df, c.df, check_like=True)  # the rows get mixed up


# languages


def test_languages_filter_noop() -> None:
    """Using languages() without any selection is a noop."""
    assert_frame_equal(
        Collection.from_dir("t/data/2019-12-04").languages().df,
        Collection.from_dir("t/data/2019-12-04").df,
    )


def test_languages_filter_in() -> None:
    """Use languages() to filter books in."""
    c = Collection.from_dir("t/data/2019-12-04")

    c.languages("fr")

    remaining = set(c.df.Language)
    assert remaining == {"fr"}, "Only the selected language"


def test_languages_filter_out() -> None:
    """Use languages() to filter books out."""
    c = Collection.from_dir("t/data/2019-12-04")

    c.languages("fr", exclude=True)

    remaining = set(c.df.Language)
    assert "fr" not in remaining, "Not the excluded language"
    assert "en" in remaining, "Does include others"


def test_languages_filter_comprehensive() -> None:
    """All the books are either included or excluded."""
    c = Collection.from_dir("t/data/2019-12-04")
    df = pd.concat(
        [
            Collection.from_dir("t/data/2019-12-04").languages("fr", exclude=True).df,
            Collection.from_dir("t/data/2019-12-04").languages("fr").df,
        ]
    )
    assert_frame_equal(df, c.df, check_like=True)  # the rows get mixed up


# categories


def test_categories_filter_noop() -> None:
    """Using categories() without any selection is a noop."""
    assert_frame_equal(
        Collection.from_dir("t/data/2019-12-04").categories().df,
        Collection.from_dir("t/data/2019-12-04").df,
    )


def test_categories_filter_in() -> None:
    """Use categories() to filter books in."""
    c = Collection.from_dir("t/data/2019-12-04")

    c.categories("novels")

    remaining = set(c.df.Category)
    assert remaining == {"novels"}, "Only the selected category"


def test_categories_filter_out() -> None:
    """Use categories() to filter books out."""
    c = Collection.from_dir("t/data/2019-12-04")

    c.categories("novels", exclude=True)

    remaining = set(c.df.Category)
    assert "novels" not in remaining, "Not the excluded category"
    assert "articles" in remaining, "Does include others"


def test_categories_filter_comprehensive() -> None:
    """All the books are either included or excluded."""
    c = Collection.from_dir("t/data/2019-12-04")
    df = pd.concat(
        [
            Collection.from_dir("t/data/2019-12-04").categories("novels", exclude=True).df,
            Collection.from_dir("t/data/2019-12-04").categories("novels").df,
        ]
    )
    assert_frame_equal(df, c.df, check_like=True)  # the rows get mixed up


# borrowed


def test_borrowed_filter_noop() -> None:
    """Using borrowed() without any selection is a noop."""
    c = Collection.from_dir("t/data/2019-12-04")

    c.borrowed()

    remaining = set(c.df.Borrowed)
    assert remaining == {True, False}


def test_borrowed_filter_in() -> None:
    """Use borrowed() to filter books in."""
    c = Collection.from_dir("t/data/2019-12-04")

    c.borrowed(True)

    remaining = set(c.df.Borrowed)
    assert remaining == {True}


def test_borrowed_filter_out() -> None:
    """Use borrowed() to filter books out."""
    c = Collection.from_dir("t/data/2019-12-04")

    c.borrowed(False)

    remaining = set(c.df.Borrowed)
    assert remaining == {False}


# chaining filters


def test_chaining() -> None:
    """Test that filters chain correctly."""
    # fmt: off
    c = (
        Collection.from_dir("t/data/2019-12-04")
        .shelves("pending")
        .borrowed(True)
        .languages("fr")
    )
    # fmt: on

    assert_frame_equal(
        c.df, c.all[(c.all.Shelf == "pending") & c.all.Borrowed & (c.all.Language == "fr")]
    )

    # again with different filters
    c = (
        Collection.from_dir("t/data/2019-12-04")
        .shelves("pending")
        .categories("graphic")
        .languages("fr", exclude=True)
        .borrowed(False)
    )

    assert_frame_equal(
        c.df,
        c.all[
            (c.all.Shelf == "pending")
            & (c.all.Category == "graphic")
            & (c.all.Language == "fr")
            & ~c.all.Borrowed
        ],
    )
