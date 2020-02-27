# vim: ts=4 : sw=4 : et

from reading.config import (
    category_patterns, config, date_columns,
    df_columns, metadata_prefer)


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

def test_config():
    assert config('goodreads.user'), 'fetched a key that exists'
    assert not config('blah.blah'), '"fetched" a key that does not exist'

