# vim: ts=4 : sw=4 : et

from reading.config import (
    Config, category_patterns, date_columns, df_columns, merge_preferences,
    metadata_prefer)


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
        "Language",
        "Pages",
        "Gender",
        "Nationality",
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

def test_config_import():
    """Test the config import, as used in the codebase."""
    from reading.config import config
    assert config('goodreads.user'), 'fetched a key that exists'
    assert not config('blah.blah'), '"fetched" a key that does not exist'


def test_config():
    """Test the config object."""
    config = Config({
        "goodreads": {
            "user": 1234567890,
        },
    })

    assert config("goodreads.user"), "fetched a key that exists"
    assert not config("blah.blah"), "'fetched' a key that does not exist"

    assert config("kindle.words_per_page") == 390, "Some keys have a default value"

    config = Config.from_file("data/config.yml")  # created from a file

    assert config("goodreads.user"), "fetched a key that exists"
    assert not config("blah.blah"), "'fetched' a key that does not exist"

    assert Config.from_file("/does/not/exist"), "created from a missing file"


def test_config_reset():
    """Test the reset method."""
    config = Config({"key": "value"})
    assert config("key") == "value", "key exists"

    config.reset()
    assert not config("key"), "key no longer exists"

    config.reset({"key": "other"})
    assert config("key") == "other", "key has been changed"
