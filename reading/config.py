# vim: ts=4 : sw=4 : et

import yaml

import attr


SHELVES = {"pending", "elsewhere", "library", "ebooks", "kindle", "to-read"}
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
        "merge": "first",
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
        "merge": "first",
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
        "merge": "min",
    },
    {
        "name": "Started",
        "store": ["goodreads", "scraped"],
        "type": "date",
        "merge": "min",
    },
    {
        "name": "Read",
        "store": ["goodreads", "scraped"],
        "type": "date",
        "merge": "max",
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
        "merge": "first",
    },
    {
        "name": "Nationality",
        "store": ["authors"],
        "merge": "first",
    },
    {
        "name": "Description",
        "store": ["authors"],
    },
    {
        "name": "_Mask",
        "store": [],
        "merge": "any",
    },
]


# columns for various CSVs (eg goodreads, ebooks)
def df_columns(store):
    """Return a list of the columns that should be included in $store."""
    return [col["name"] for col in _COLUMNS if store in col["store"]]


def date_columns(store):
    """Return a list of the columns that should be treated as dates."""
    return [col["name"] for col in _COLUMNS if store in col["store"] and col.get("type") == "date"]


def metadata_prefer(preference):
    """Return a list of columns whose values should be prioritised when assembling the metadata.

    Where $preference should be one of "work" (for the Goodreads work) or
    "book" (for the ebook).
    """
    return [col["name"] for col in _COLUMNS if col.get("prefer") == preference]


def merge_preferences():
    """Return a dict specifying how volumes of the same book should be merged."""
    return {
        **{"BookId": "first"},
        **{col["name"]: col["merge"] for col in _COLUMNS if "merge" in col},
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

@attr.s
class Config:
    """configuration."""

    _conf = attr.ib()

    @classmethod
    def from_file(cls, filename="data/config.yml"):
        """Create from $filename."""
        try:
            with open(filename) as fh:
                conf = yaml.safe_load(fh)
        except FileNotFoundError:
            conf = {}

        return cls(conf)

    def __call__(self, key):
        value = self._conf

        for segment in key.split("."):
            try:
                value = value[segment]
            except KeyError:
                # TODO use defaults and/or emit warning
                return None

        return value

    def reset(self, conf=None):
        """Set to an empty configuration."""
        self._conf = conf or {}


config = Config.from_file()  # pylint: disable=invalid-name


################################################################################

def main(args):
    print(config(args.key))
