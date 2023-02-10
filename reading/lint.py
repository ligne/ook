# vim: ts=4 : sw=4 : et

"""Find problems with the data in the collection."""

import datetime as dt

from jinja2 import Template
import pandas as pd

from .collection import Collection, _process_fixes
from .config import Config


################################################################################

_LINTERS = {}


def linter(func):
    """Register a linter function."""
    _LINTERS[func.__name__] = func
    return func


################################################################################


@linter
def lint_missing_pagecount():
    """Missing a pagecount."""
    c = Collection.from_dir().shelves("to-read", exclude=True)
    return {
        "df": c.df[c.df.Pages.isnull()],
        "template": """
{%- for entry in df.itertuples() %}
{{entry.Author}}, {{entry.Title}}
{%- endfor %}

""",
    }


@linter
def lint_words_per_page():
    """Unusual words per page."""
    c = Collection.from_dir(fixes=None, merge=True).shelves("kindle")

    df = c.df
    df["wpp"] = df.Words / df.Pages

    return {
        "df": df[(df.wpp < 150) | (df.wpp > 700) & (df.Pages > 10)],
        "template": """
{%- for entry in df.itertuples() %}
{{entry.Author}}, {{entry.Title}}
  {{entry.wpp | int}} words per page, {{entry.Pages | int}} pages
{%- endfor %}

""",
    }


@linter
def lint_missing_category():
    """Missing a category."""
    c = Collection.from_dir()
    return {
        "df": c.df[c.df.Category.isnull()],
        "template": """
{%- for entry in df.itertuples() %}
{{entry.Author}}, {{entry.Title}}
{%- endfor %}

""",
    }


@linter
def lint_missing_published_date():
    """Missing a published date."""
    c = Collection.from_dir().shelves("kindle", "to-read", exclude=True)

    return {
        "df": c.df[c.df.Published.isnull()],
        "template": """
{%- for entry in df.itertuples() %}
{{entry.Author}}, {{entry.Title}}
{%- endfor %}

""",
    }


@linter
def lint_dates():
    """Finished date before Started date."""
    c = Collection.from_dir().shelves("read")
    return {
        "df": c.df[c.df.Read < c.df.Started],
        "template": """
{%- for entry in df.itertuples() %}
{{entry.Author}}, {{entry.Title}}: {{entry.Started.date()}} - {{entry.Read.date()}}
{%- endfor %}

""",
    }


@linter
def lint_started_before_added():
    """Start date before Added date."""
    c = Collection.from_dir()
    return {
        "df": c.df[c.df.Started < c.df.Added],
        "template": """
{%- for entry in df.itertuples() %}
{{entry.Author}}, {{entry.Title}}: {{entry.Added.date()}} - {{entry.Started.date()}}
{%- endfor %}

""",
    }


@linter
def lint_missing_language():
    """Missing a langugage."""
    c = Collection.from_dir()
    return {
        "df": c.df[c.df.Language.isnull()],
        "template": """
{%- for entry in df.itertuples() %}
{{entry.Author}}, {{entry.Title}} https://www.goodreads.com/book/show/{{entry.Index}}
{%- endfor %}

""",
    }


@linter
def lint_scheduled_misshelved():
    """Scheduled books on wrong shelves."""
    c = Collection.from_dir().shelves("read", "currently-reading", "to-read")
    return {
        "df": c.df[c.df.Scheduled.notnull()],
        "template": """
{%- for entry in df.itertuples() %}
{{entry.Author}}, {{entry.Title}}
    {{entry.Shelf}}
{%- endfor %}

""",
    }


# scheduled books by authors i've already read this year
# FIXME this doesn't actually work very well
@linter
def lint_overscheduled(config):
    """Multiple scheduled books by the same author."""
    # get the automatically-scheduled books
    c = Collection.from_dir(merge=True)
    c._df.Scheduled = pd.NaT  # pylint: disable=protected-access
    c.set_schedules(config("scheduled"))
    automatic = c.df.Scheduled

    df = Collection.from_dir(merge=True).df

    today = dt.date.today()

    # get authors that are/have been read this calendar year, or are
    # automatically scheduled this year
    bad_authors = set(
        df[
            (df.Read.dt.year == today.year)
            | (df.Shelf == "currently-reading")
            | (automatic.dt.year == today.year)
        ].AuthorId
    )

    # find books manually scheduled for this year that aren't in the bad list
    df = df[
        automatic.isnull()
        & df.AuthorId.isin(bad_authors)
        & (df.Scheduled.dt.year == today.year)
        & (df.Shelf != "currently-reading")  # too late now!
    ]

    return {
        "df": df,
        "template": """
{%- for entry in df.itertuples() %}
{{entry.Author}}, {{entry.Title}}
{%- endfor %}

""",
    }


@linter
def lint_scheduling(config):
    """Mis-scheduled books."""
    c = Collection.from_dir()

    got = c.df.Scheduled.copy()
    c.set_schedules(config("scheduled"))
    df = c.df.assign(Got=got)

    horizon = dt.date.today().year + 3

    return {
        "df": df[
            df.Scheduled.notna()
            & (df.Scheduled.dt.year < horizon)
            & (df.Got.dt.year != df.Scheduled.dt.year)
        ],
        "template": """
{%- for entry in df.itertuples() %}
{{entry.Author}}, {{entry.Title}}:  {{entry.Scheduled.year}}, not {{entry.Got.year}}
  https://www.goodreads.com/book/show/{{entry.Index}}
{%- endfor %}

""",
    }


@linter
def lint_duplicates():
    """Duplicate books."""
    acceptable = [
        "library, kindle",
        "ebooks, kindle",
    ]

    df = Collection.from_dir(merge=True).df

    # FIXME move this into the Collection and make it non-manky
    df = df.groupby("Work", as_index=False).filter(lambda x: len(x) > 1)
    df = df.groupby("Work", as_index=False).aggregate(
        {
            "Author": "first",
            "Title": "first",
            "Work": "first",
            "Shelf": lambda x: ", ".join(list(x)),
        }
    )
    df = df.groupby("Work").filter(lambda x: ~x.Shelf.isin(acceptable))

    return {
        "df": df,
        "template": """
{%- for entry in df.itertuples() %}
{{entry.Author}}, {{entry.Title}}
    {{entry.Shelf}}
{%- endfor %}

""",
    }


# books in dubious formats
@linter
def lint_binding():
    """Bad binding."""
    good_bindings = [
        "Paperback",
        "paperback",
        "Hardcover",
        "Mass Market Paperback",
        "Kindle Edition",
        "ebook",
        "Poche",
        "Broché",
        "Relié",
        "Board book",
        "Unknown Binding",
    ]
    c = Collection.from_dir().shelves("kindle", exclude=True)
    return {
        "df": c.df[~(c.df.Binding.isin(good_bindings) | c.df.Binding.isnull())],
        "template": """
{%- for binding, books in df.groupby('Binding') %}
{{binding}}:
  {%- for entry in books.itertuples() %}
  * {{entry.Author}}, {{entry.Title}}
  {%- endfor %}
{%-endfor %}

""",
    }


@linter
def missing_nationality():
    """Missing author nationality."""
    df = Collection.from_dir().shelves("kindle", exclude=True).df

    return {
        "df": df[df.Nationality.isnull()].sort_values(["Author", "Title"]),
        "template": """
{%- for entry in df.itertuples() %}
{{entry.Author}}, {{entry.Title}}
{%- endfor %}

""",
    }


@linter
def missing_gender():
    """Missing author gender."""
    df = Collection.from_dir().shelves("kindle", exclude=True).df

    return {
        "df": df[df.Gender.isnull()].sort_values(["Author", "Title"]),
        "template": """
{%- for entry in df.itertuples() %}
{{entry.Author}}, {{entry.Title}}
{%- endfor %}

""",
    }


@linter
def lint_missing_borrowed():
    """Not at home but not marked as borrowed."""
    c = Collection.from_dir().shelves("elsewhere", "library").borrowed(False)
    return {
        "df": c.df,
        "template": """
{%- for entry in df.itertuples() %}
{{entry.Author}}, {{entry.Title}}
{%- endfor %}

""",
    }


@linter
def lint_extraneous_borrowed():
    """To-read but marked as borrowed."""
    c = Collection.from_dir().shelves("to-read").borrowed(True)
    return {
        "df": c.df,
        "template": """
{%- for entry in df.itertuples() %}
{{entry.Author}}, {{entry.Title}}
{%- endfor %}

""",
    }


@linter
def lint_needs_returning():
    """Borrowed books to return."""
    c = Collection.from_dir().shelves("read").borrowed(True)
    return {
        "df": c.df,
        "template": """
{%- for entry in df.itertuples() %}
{{entry.Author}}, {{entry.Title}}
{%- endfor %}

""",
    }


@linter
def lint_not_rated():
    """Read but not yet rated."""
    c = Collection.from_dir().shelves("read")
    return {
        "df": c.df[c.df.Rating == 0].sort_values("Read"),
        "template": """
{%- for entry in df.itertuples() %}
{{entry.Author}}, {{entry.Title}}, https://www.goodreads.com/review/edit/{{entry.Index}}
{%- endfor %}

""",
    }


# find unnecessary fixes
# FIXME update
@linter
def lint_fixes(config):
    """Unneeded fixes."""
    c = Collection.from_dir(fixes=None)

    fixes = _process_fixes(config("fixes"))
    errors = []

    for book_id, fix in fixes.iterrows():
        if book_id not in c.df.index:
            errors.append("Book {} does not exist".format(book_id))
            continue
        for col, value in fix[fix.notnull()].items():
            if c.df.loc[book_id, col] == value:
                errors.append("Unnecessary entry [{},{}]".format(book_id, col))

    return {
        "df": errors,
        "template": """
{%- for entry in df %}
{{entry}}
{%- endfor %}

""",
    }


################################################################################


def main(args, config: Config) -> None:
    for name, func in _LINTERS.items():
        if args.pattern and args.pattern not in name:
            continue

        import inspect

        # FIXME update all the lint functions and get rid of this
        if inspect.getfullargspec(func).args:
            report = func(config)
        else:
            report = func()

        # FIXME
        if report is None or "df" not in report:
            print(report)
            continue

        if not len(report["df"]):  # pylint: disable=len-as-condition
            continue

        title = func.__doc__
        if title.endswith("."):
            title = title[:-1]

        print(f"=== {title} ===")

        if "template" not in report:
            continue

        print(Template(report["template"]).render(df=report["df"]))
