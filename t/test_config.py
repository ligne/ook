# vim: ts=4 : sw=4 : et

from __future__ import annotations

from reading.config import (
    Config,
    category_patterns,
    date_columns,
    df_columns,
    merge_preferences,
)


def test_df_colums() -> None:
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
        "Binding",
        "Pages",
        "Started",
        "Read",
    ], "Columns for scraped.csv"


def test_date_columns() -> None:
    assert date_columns("goodreads") == [
        "Scheduled",
        "Added",
        "Started",
        "Read",
    ], "Date columns for goodreads"


################################################################################


def test_category_patterns() -> None:
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
        [
            "non-fiction",
            "education",
            "theology",
            "linguistics",
            "architecture",
            "history",
            "art",
            "very-short-introductions",
        ],
        ["novels", "fiction"],
    ]


################################################################################


def test_merge_preferences() -> None:
    assert merge_preferences() == {
        "Added": "min",
        "Author": "first",
        "AuthorId": "first",
        "AvgRating": "first",
        "Binding": "first",
        "BookId": "first",
        "Borrowed": "first",
        "Category": "first",
        "Gender": "first",
        "Language": "first",
        "_Mask": "any",
        "Nationality": "first",
        "Pages": "sum",
        "Published": "first",
        "Rating": "mean",
        "Read": "max",
        "Scheduled": "first",
        "Series": "first",
        "SeriesId": "first",
        "Shelf": "first",
        "Started": "min",
        "Title": "first",
        "Words": "sum",
        "Work": "first",
    }


################################################################################


def test_config() -> None:
    """Test the config object."""
    config = Config(
        {
            "goodreads": {
                "user": 1234567890,
            },
        }
    )

    assert config("goodreads.user") == 1234567890, "fetched a key that exists"
    assert not config("blah.blah"), "'fetched' a key that does not exist"

    assert config("kindle.words_per_page") == 390, "Some keys have a default value"


def test_config_from_file() -> None:
    config = Config.from_file("t/data/2019-12-04/config.yml")  # created from a file

    assert config("kindle.words_per_page") == 123, "fetched a key that exists"
    assert not config("blah.blah"), "'fetched' a key that does not exist"

    assert Config.from_file("/does/not/exist"), "created from a missing file"


def test_config_reset() -> None:
    """Test the reset method."""
    config = Config({"key": "value"})
    assert config("key") == "value", "key exists"

    config.reset()
    assert not config("key"), "key no longer exists"

    config.reset({"key": "other"})
    assert config("key") == "other", "key has been changed"
