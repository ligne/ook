# vim: ts=4 : sw=4 : et

import pytest

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

from reading.collection import Collection, _get_gr_books, _get_kindle_books, _process_fixes


################################################################################

def test__get_gr_books():
    df = _get_gr_books(csv="t/data/goodreads-2019-12-04.csv")

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
    ]

    assert set(df.Category) == {
        'novels',
        'short-stories',
        'non-fiction',
        'graphic',
        np.nan
    }

    unmerged = _get_gr_books(csv="t/data/goodreads-2019-12-04.csv", merge=False)
    assert len(unmerged) == 139
    assert not unmerged.index.hasnans

    merged = _get_gr_books(csv="t/data/goodreads-2019-12-04.csv", merge=True)
    assert len(merged) == 136
    assert not merged.index.hasnans


def test_goodreads_merge():
    unmerged = _get_gr_books(csv="t/data/goodreads-2019-12-04.csv")
    merged = _get_gr_books(csv="t/data/goodreads-2019-12-04.csv", merge=True)

    assert sorted(list(unmerged.columns) + ["Volume"]) == sorted(merged.columns)

    assert not unmerged.index.equals(merged.index), "Merging goodreads books had some effect"
    assert len(unmerged.index) > len(merged.index), "Merging goodreads books had some effect"

    assert not unmerged.index.hasnans, "No NaNs in unmerged goodreads index"
    assert not merged.index.hasnans, "No NaNs in merged goodreads index"

    assert merged.index.difference(unmerged.index).empty, "merged is a subset of unmerged"

    assert 0 not in merged.index, "Index should be BookIds"
    assert 3 not in merged.index, "Check it's searching by ID not index"


def test_kindle_merge():
    unmerged = _get_kindle_books()
    merged = _get_kindle_books(merge=True)

    assert sorted(list(unmerged.columns) + ["Volume"]) == sorted(merged.columns)

    assert not unmerged.index.equals(merged.index), "Merging kindle books had some effect"
    assert len(unmerged.index) > len(merged.index), "Merging kindle books had some effect"

    assert not unmerged.index.hasnans, "No NaNs in unmerged kindle index"
    assert not merged.index.hasnans, "No NaNs in merged kindle index"

    assert merged.index.difference(unmerged.index).empty, "merged is a subset of unmerged"

    assert 0 not in merged.index, "Index should be BookIds"
    assert 3 not in merged.index, "Check it's searching by ID not index"


def test__get_kindle_books():
    df = _get_kindle_books(csv="t/data/ebooks-2019-12-04.csv")

    assert list(df.columns) == [
        "Author",
        "Title",
        "Category",
        "Language",
        "Words",
        "Added",
        "Pages",
        "Shelf",
        "Binding",
        "Borrowed",
    ]

    assert set(df.Binding) == {'ebook'}, 'ebook binding is always ebook'
    assert set(df.Borrowed) == {False}, 'ebooks are never borrowed'
    assert set(df.Shelf) == {'kindle'}, 'ebook shelf is always kindle'

    assert set(df.Category) == {
        'articles',
        'non-fiction',
        'novels',
        'short-stories',
    }

#     eq_(list(zip(df.columns, df.dtypes)), [
#     ])

    b = df.loc['non-fiction/pg14154.mobi']  # A Tale of Terror

    assert str(b.Added.date()) == '2013-02-06', 'Added is sensible'

    # FIXME do we actually care?
    assert df[df.Author.isnull()].empty, "Every ebook has an author"


@pytest.mark.slow
def test_collection_crudely(collection):
    c = Collection()
    assert c.df.equals(Collection().df), "Same collection is the same"

    assert Collection(merge=True, metadata=False)
    assert Collection(merge=True, metadata=True)
    assert Collection(dedup=True)
    assert Collection(dedup=True, merge=True)
    assert Collection(fixes=False)
    assert Collection(metadata=False)

    assert (
        len(collection("2019-12-04", merge=True, metadata=True).df) == 397
    ), "Merged collection is a sensible length"


def test_collection(collection):
    df = collection("2019-12-04").df

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
        "Gender",
        "Nationality",
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


def test_collection_shelves(collection):
    assert_frame_equal(
        collection("2019-12-04").shelves().df,
        collection("2019-12-04").df
    )

    c = collection("2019-12-04")
    assert set(c.shelves(["library"]).df.Shelf) == {
        "library"
    }, "Only the selected shelf"

    c = collection("2019-12-04")
    assert (
        set(c.shelves(exclude=["library"]).df.Shelf) & {"library"} == set()
    ), "Not the excluded shelf"

    df = pd.concat([
        collection("2019-12-04").shelves(exclude=["library"]).df,
        collection("2019-12-04").shelves(include=["library"]).df,
    ])
    assert set(df.index) == set(collection("2019-12-04").df.index)


def test_collection_languages(collection):
    assert_frame_equal(
        collection("2019-12-04").languages().df,
        collection("2019-12-04").df
    )

    assert_frame_equal(
        collection("2019-12-04").languages().df, collection("2019-12-04").df
    )

    assert set(collection("2019-12-04").languages(["fr"]).df.Language) == {
        "fr"
    }, "Only the selected language"

    assert (
        set(collection("2019-12-04").languages(exclude=["fr"]).df.Language) & {"fr"} == set()
    ), "Not the excluded language"

    df = pd.concat([
        collection("2019-12-04").languages(exclude=["fr"]).df,
        collection("2019-12-04").languages(include=["fr"]).df,
    ])
    assert (
        set(df.index) == set(collection("2019-12-04").df.index)
    ), "include + exclude = all languages"


def test_collection_categories(collection):
    assert_frame_equal(
        collection("2019-12-04").categories().df,
        collection("2019-12-04").df
    )

    assert set(collection("2019-12-04").categories(["novels"]).df.Category) == {
        "novels"
    }, "Only the selected category"

    assert (
        set(collection("2019-12-04").categories(exclude=["novels"]).df.Category)
        & {"novels"}
        == set()
    ), "Not the excluded category"

    df = pd.concat([
        collection("2019-12-04").categories(exclude=["novels"]).df,
        collection("2019-12-04").categories(include=["novels"]).df,
    ])
    assert (
        set(df.index) == set(collection("2019-12-04").df.index)
    ), "include + exclude = all categories"


def test_collection_borrowed(collection):
    assert set(collection("2019-12-04").borrowed().df.Borrowed) == {True, False}
    assert set(collection("2019-12-04").borrowed(True).df.Borrowed) == {True}
    assert set(collection("2019-12-04").borrowed(False).df.Borrowed) == {False}


def test_collection_filter(collection):
    assert_frame_equal(
        collection("2019-12-04").filter().df, collection("2019-12-04").df
    )  # filter() does nothing without arguments

    assert_frame_equal(
        collection("2019-12-04").filter(borrowed=True).df,
        collection("2019-12-04").borrowed(True).df,
    )  # filter() does the same as the individual methods

    assert_frame_equal(
        collection("2019-12-04").filter(shelves=["library"]).df,
        collection("2019-12-04").shelves(["library"]).df,
    )  # filter() does the same as the individual methods

    assert_frame_equal(
        collection("2019-12-04").filter(languages=["fr"]).df,
        collection("2019-12-04").languages(["fr"]).df,
    )  # filter() does the same as the individual methods

    assert_frame_equal(
        collection("2019-12-04").filter(categories=["graphic"]).df,
        collection("2019-12-04").categories(["graphic"]).df,
    )  # filter() does the same as the individual methods

    assert_frame_equal(
        collection("2019-12-04").filter(shelves=["pending"], borrowed=True).df,
        collection("2019-12-04").borrowed(True).shelves(["pending"]).df,
    )  # Same, but with more than one filter


def test_read(collection):
    c = collection("2019-12-04")

    df = c.read

    assert set(df.Shelf) == {"read", "currently-reading"}, "Only expected shelves"
    assert 10374 in df.index, "Read book is there"

    assert 38290 not in df.index, "Unread book is not"
    assert 38290 in c.all.index, "Unread book is in the collection however"

    assert_frame_equal(
        collection("2019-12-04").categories(["novels"]).read,
        collection("2019-12-04").read,
    )  # Same result even with a filtered frame


# def test_recent_authorids(collection):
#     c = collection("2019-12-04")


def test_read_authorids(collection):
    c = collection("2019-12-04")

    assert c.read_authorids == {
        1654,
        3354,
        4750,
        4785,
        7628,
        9343,
        9693,
        228089,
        874602,
        2778055,
        5807106,
    }

    assert 2778055 in c.read_authorids, "Author in currently-reading is included"


def test_read_nationalities(collection):
    c = collection("2019-12-04")

    assert c.read_nationalities == {"fr", "us", "jp", "gb", "be"}


def test__process_fixes():
    assert not _process_fixes({}), 'No fixes to apply'
