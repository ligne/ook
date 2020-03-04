# vim: ts=4 : sw=4 : et

from reading.config import (
    category_patterns, config, date_columns,
    df_columns, metadata_prefer, merge_preferences)


def test_df_colums():
    assert df_columns("goodreads") == [
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
    ], "Columns for goodreads.csv"

    assert df_columns("books") == [
        "BookId",
        "Author",
        "AuthorId",
        "Title",
        "Work",
        "Category",
        "Series",
        "SeriesId",
        "Entry",
        "Published",
        "Language",
        "Pages",
    ], "Columns for books.csv"

    assert df_columns("authors") == [
        "QID",
        "Author",
        "Gender",
        "Nationality",
        "Description",
    ], "Columns for authors.csv"

    assert df_columns("scraped") == [
        "Pages",
        "Started",
        "Read",
    ], "Columns for scraped.csv"

    assert df_columns("metadata") == [
        "Author",
        "AuthorId",
        "Title",
        "Work",
        "Series",
        "SeriesId",
        "Entry",
        "Published",
        "Pages",
    ], "Columns for metadata.csv"


def test_date_columns():
    assert date_columns("goodreads") == [
        "Scheduled",
        "Added",
        "Started",
        "Read",
    ], "Date columns for goodreads"


################################################################################

def test_category_patterns():
    (patterns, guesses) = category_patterns()
    assert patterns == [
        ["graphic", "graphic-novels", "comics", "graphic-novel"],
        [
            "short-stories",
            "short-story",
            "nouvelles",
            "short-story-collections",
            "relatos-cortos",
        ],
        ["non-fiction", "nonfiction", "essays"],
        ["novels", "novel", "roman", "romans"],
    ]

    assert guesses == [
        ["non-fiction", "education", "theology", "linguistics"],
        ["novels", "fiction"],
    ]


################################################################################

def test_metadata_prefer():
    assert metadata_prefer("work") == [
        "Author",
        "AuthorId",
        "Title",
        "Work",
        "Series",
        "SeriesId",
        "Entry",
        "Published",
        "Pages",
    ], "Prefer the goodreads work's metadata"

    assert metadata_prefer("book") == ["Language"], "Prefer the ebook's metadata"


################################################################################

def test_merge_preferences():
    assert merge_preferences("goodreads") == {
        "Added": "first",
        "AuthorId": "first",
        "AvgRating": "first",
        "Binding": "first",
        "BookId": "first",
        "Borrowed": "first",
        "Category": "first",
        "Language": "first",
        "Pages": "sum",
        "Published": "first",
        "Rating": "mean",
        "Read": "last",
        "Scheduled": "first",
        "Series": "first",
        "SeriesId": "first",
        "Shelf": "first",
        "Started": "first",
        "Work": "first",
    }, "What columns to prefer when merging goodreads volumes"

    assert merge_preferences("goodreads") == {
        **{
            col: "first"
            for col in df_columns("goodreads")
            if col not in ("Author", "Title", "Entry", "Volume")
        },
        **{"Pages": "sum", "BookId": "first", "Rating": "mean", "Read": "last"},
    }

    assert merge_preferences("ebooks") == {
        "Added": "first",
        "BookId": "first",
        "Category": "first",
        "Language": "first",
        "Words": "sum",
    }, "What columns to prefer when merging ebook volumes"

    assert merge_preferences("ebooks") == {
        **{
            col: "first"
            for col in df_columns("ebooks")
            if col not in ("Author", "Title", "Entry", "Volume")
        },
        **{"Words": "sum", "BookId": "first"},
    }


################################################################################

def test_config():
    assert config('goodreads.user'), 'fetched a key that exists'
    assert not config('blah.blah'), '"fetched" a key that does not exist'

