# vim: ts=4 : sw=4 : et

import yaml


SHELVES = {"pending", "elsewhere", "library", "ebooks", "kindle"}
CATEGORIES = {"novels", "short-stories", "non-fiction", "graphic", "articles"}


_COLUMNS = [
    {
        "name": "QID",
        "store": ["authors"],
    },
    {
        "name": "BookId",
        "store": ["books"],
        "merge": "first",
    },
    {
        "name": "Author",
        "store": ["goodreads", "ebooks", "books", "authors", "metadata"],
        "prefer": "work",
    },
    {
        "name": "AuthorId",
        "store": ["goodreads", "books", "metadata"],
        "prefer": "work",
        "merge": "first",
    },
    {
        "name": "Title",
        "store": ["goodreads", "ebooks", "books", "metadata"],
        "prefer": "work",
    },
    {
        "name": "Work",
        "store": ["goodreads", "books", "metadata"],
        "prefer": "work",
        "merge": "first",
    },
    {
        "name": "Shelf",
        "store": ["goodreads"],
        "merge": "first",
    },
    {
        "name": "Category",
        "store": ["goodreads", "ebooks", "books"],
        "merge": "first",
    },
    {
        "name": "Scheduled",
        "store": ["goodreads"],
        "type": "date",
        "merge": "first",
    },
    {
        "name": "Borrowed",
        "store": ["goodreads"],
        "merge": "first",
    },
    {
        "name": "Series",
        "store": ["goodreads", "books", "metadata"],
        "prefer": "work",
        "merge": "first",
    },
    {
        "name": "SeriesId",
        "store": ["goodreads", "books", "metadata"],
        "prefer": "work",
        "merge": "first",
    },
    {
        "name": "Entry",
        "store": ["goodreads", "books", "metadata"],
        "prefer": "work",
    },
    {
        "name": "Binding",
        "store": ["goodreads"],
        "merge": "first",
    },
    {
        "name": "Published",
        "store": ["goodreads", "books", "metadata"],
        # Can't convert Published to a date as pandas' range isn't big enough
        "prefer": "work",
        "merge": "first",
    },
    {
        "name": "Language",
        "store": ["goodreads", "ebooks", "books"],
        "prefer": "book",
        "merge": "first",
    },
    {
        "name": "Pages",
        "store": ["goodreads", "books", "scraped", "metadata"],
        "prefer": "work",
        "merge": "sum",
    },
    {
        "name": "Words",
        "store": ["ebooks"],
        "merge": "sum",
    },
    {
        "name": "Added",
        "store": ["goodreads", "ebooks"],
        "type": "date",
        "merge": "first",
    },
    {
        "name": "Started",
        "store": ["goodreads", "scraped"],
        "type": "date",
        "merge": "first",
    },
    {
        "name": "Read",
        "store": ["goodreads", "scraped"],
        "type": "date",
        "merge": "last",
    },
    {
        "name": "Rating",
        "store": ["goodreads"],
        "merge": "mean",
    },
    {
        "name": "AvgRating",
        "store": ["goodreads"],
        "merge": "first",
    },
    {
        "name": "Gender",
        "store": ["authors"],
    },
    {
        "name": "Nationality",
        "store": ["authors"],
    },
    {
        "name": "Description",
        "store": ["authors"],
    },
]


# columns for various CSVs (eg goodreads, ebooks)
def df_columns(store):
    return [col["name"] for col in _COLUMNS if store in col["store"]]


def date_columns(store):
    return [col["name"] for col in _COLUMNS if store in col["store"] and col.get("type") == "date"]


def metadata_prefer(preference):
    return [col["name"] for col in _COLUMNS if col.get("prefer") == preference]


def merge_preferences(store):
    return {
        **{"BookId": "first"},
        **{
            col["name"]: col["merge"]
            for col in _COLUMNS
            if store in col["store"] and "merge" in col
        },
    }


################################################################################

_CATEGORIES = {
    "graphic": (
        ["graphic-novels", "comics", "graphic-novel"],
    ),
    "short-stories": (
        ["short-story", "nouvelles", "short-story-collections", "relatos-cortos"],
    ),
    "non-fiction": (
        ["nonfiction", "essays"],
        ['education', "theology", "linguistics"],
    ),
    "novels": (
        ["novel", "roman", "romans"],
        ["fiction"],
    ),
}


def category_patterns():
    patterns = []
    guesses = []

    for name, pats in _CATEGORIES.items():
        patterns.append([name] + pats[0])
        if len(pats) > 1:
            guesses.append([name] + pats[1])

    return (patterns, guesses)


################################################################################

# value = config('key.name')
def config(key):
    with open('data/config.yml') as fh:
        conf = yaml.safe_load(fh)

    for segment in key.split('.'):
        try:
            conf = conf[segment]
        except KeyError:
            # use defaults and/or emit warning
            return None

    return conf


################################################################################

def main(args):
    print(config(args.key))

