# vim: ts=4 : sw=4 : et

from jinja2 import Template

from .collection import Collection, _process_fixes
from .config import config


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
    c = Collection.from_dir().shelves(exclude=["to-read"])
    return {
        'df': c.df[c.df.Pages.isnull()],
        'template': """
{%- for entry in df.itertuples() %}
{{entry.Author}}, {{entry.Title}}
{%- endfor %}

""",
    }


@linter
def lint_words_per_page():
    """Unusual words per page."""
    c = Collection.from_dir(fixes=None, merge=True).shelves(["kindle"])

    df = c.df
    df['wpp'] = df.Words / df.Pages

    return {
        'df': df[(df.wpp < 150) | (df.wpp > 700) & (df.Pages > 10)],
        'template': """
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
        'df': c.df[c.df.Category.isnull()],
        'template': """
{%- for entry in df.itertuples() %}
{{entry.Author}}, {{entry.Title}}
{%- endfor %}

""",
    }


@linter
def lint_missing_published_date():
    """Missing a published date."""
    c = Collection.from_dir().shelves(exclude=["kindle", "to-read"])

    return {
        'df': c.df[c.df.Published.isnull()],
        'template': """
{%- for entry in df.itertuples() %}
{{entry.Author}}, {{entry.Title}}
{%- endfor %}

""",
    }


@linter
def lint_dates():
    """Finished date before Started date."""
    c = Collection.from_dir().shelves(["read"])
    return {
        'df': c.df[c.df.Read < c.df.Started],
        'template': """
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
        'df': c.df[c.df.Language.isnull()],
        'template': """
{%- for entry in df.itertuples() %}
{{entry.Author}}, {{entry.Title}} https://www.goodreads.com/book/show/{{entry.Index}}
{%- endfor %}

""",
    }


@linter
def lint_scheduled_misshelved():
    """Scheduled books on wrong shelves."""
    c = Collection.from_dir().shelves(["read", "currently-reading", "to-read"])
    return {
        'df': c.df[c.df.Scheduled.notnull()],
        'template': """
{%- for entry in df.itertuples() %}
{{entry.Author}}, {{entry.Title}}
    {{entry.Shelf}}
{%- endfor %}

""",
    }


# scheduled books by authors i've already read this year
@linter
def lint_overscheduled():
    """Multiple scheduled books by the same author."""
    c = Collection.from_dir(merge=True)
    df = c.df

    import datetime
    from reading.scheduling import _set_schedules

    _set_schedules(df, config("scheduled"), col="Automatic")

    today = datetime.date.today()

    # not read or automatically scheduled this year
    bad = set(
        df[
            (df.Read.dt.year == today.year)
            | (df.Shelf == "currently-reading")
            | (df.Automatic.dt.year == today.year)
        ].AuthorId
    )

    # books that are manually scheduled but not in the list
    df = df[
        df.Automatic.isnull()
        & df.AuthorId.isin(bad)
        & (df.Scheduled.dt.year == today.year)
        & (df.Shelf != "currently-reading")
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
def lint_scheduling():
    """Mis-scheduled books."""
    c = Collection.from_dir()

    df = c.df

    from reading.scheduling import _set_schedules
    import datetime

    horizon = datetime.date.today().year + 3

    _set_schedules(df, config('scheduled'), col='Expected')

    df = df[df.Expected.notnull()]  # only automatically scheduled
    df = df[df.Expected.dt.year < horizon]
    df = df[df.Scheduled.dt.year != df.Expected.dt.year]

    return {
        'df': df,
        'template': """
{%- for entry in df.itertuples() %}
{{entry.Author}}, {{entry.Title}}:  {{entry.Expected.year}}, not {{entry.Scheduled.year}}
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
    df = df.groupby('Work').filter(lambda x: len(x) > 1)
    df = df.groupby('Work').aggregate(
        {
            'Author': 'first',
            'Title': 'first',
            'Work': 'first',
            'Shelf': lambda x: ', '.join(list(x)),
        }
    )
    df = df.groupby("Work").filter(lambda x: ~x.Shelf.isin(acceptable))

    return {
        'df': df,
        'template': """
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
        'Paperback',
        'paperback',
        'Hardcover',
        'Mass Market Paperback',
        'Kindle Edition',
        'ebook',
        'Poche',
        'Broché',
        'Relié',
        'Board book',
        "Unknown Binding",
    ]
    c = Collection.from_dir().shelves(exclude=["kindle"])
    return {
        'df': c.df[~(c.df.Binding.isin(good_bindings) | c.df.Binding.isnull())],
        'template': """
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
    df = Collection.from_dir().shelves(exclude=["kindle"]).df

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
    df = Collection.from_dir().shelves(exclude=["kindle"]).df

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
    c = Collection.from_dir().shelves(["elsewhere", "library"]).borrowed(False)
    return {
        'df': c.df,
        'template': """
{%- for entry in df.itertuples() %}
{{entry.Author}}, {{entry.Title}}
{%- endfor %}

""",
    }


@linter
def lint_extraneous_borrowed():
    """To-read but marked as borrowed."""
    c = Collection.from_dir().shelves(["to-read"]).borrowed(True)
    return {
        'df': c.df,
        'template': """
{%- for entry in df.itertuples() %}
{{entry.Author}}, {{entry.Title}}
{%- endfor %}

""",
    }


@linter
def lint_needs_returning():
    """Borrowed books to return."""
    c = Collection.from_dir().shelves(["read"]).borrowed(True)
    return {
        'df': c.df,
        'template': """
{%- for entry in df.itertuples() %}
{{entry.Author}}, {{entry.Title}}
{%- endfor %}

""",
    }


@linter
def lint_not_rated():
    """Read but not yet rated."""
    c = Collection.from_dir().shelves(["read"])
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
def lint_fixes():
    """Unneeded fixes."""
    c = Collection.from_dir(fixes=None)

    fixes = _process_fixes(config('fixes'))
    errors = []

    for book_id, fix in fixes.iterrows():
        if book_id not in c.df.index:
            errors.append('Book {} does not exist'.format(book_id))
            continue
        for col, value in fix[fix.notnull()].items():
            if c.df.loc[book_id, col] == value:
                errors.append("Unnecessary entry [{},{}]".format(book_id, col))

    return {
        'df': errors,
        'template': """
{%- for entry in df %}
{{entry}}
{%- endfor %}

""",
    }


################################################################################


def main(args):
    for name, func in _LINTERS.items():
        if args.pattern and args.pattern not in name:
            continue

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
