# vim: ts=4 : sw=4 : et

from .collection import _process_fixes
from .collection import Collection
from .config import config


def lint_missing_pagecount():
    c = Collection().shelves(exclude=["to-read"])
    return {
        'title': 'Missing a pagecount',
        'df': c.df[c.df.Pages.isnull()],
        'template': """
{%- for entry in df.itertuples() %}
{{entry.Author}}, {{entry.Title}}
{%- endfor %}

""",
    }


def lint_words_per_page():
    c = Collection(fixes=None, merge=True)

    df = c.df
    df['wpp'] = df.Words / df.Pages

    return {
        'title': 'Unusual words per page',
        'df': df[(df.wpp < 150) | (df.wpp > 700) & (df.Pages > 10)],
        'template': """
{%- for entry in df.itertuples() %}
{{entry.Author}}, {{entry.Title}}
  {{entry.wpp | int}} words per page, {{entry.Pages | int}} pages
{%- endfor %}

""",
    }


def lint_missing_category():
    c = Collection()
    return {
        'title': 'Missing a category',
        'df': c.df[c.df.Category.isnull()],
        'template': """
{%- for entry in df.itertuples() %}
{{entry.Author}}, {{entry.Title}}
{%- endfor %}

""",
    }


def lint_missing_published_date():
    c = Collection().shelves(["pending", "ebooks", "elsewhere", "read"])
    return {
        'title': 'Missing a published date',
        'df': c.df[c.df.Published.isnull()],
        'template': """
{%- for entry in df.itertuples() %}
{{entry.Author}}, {{entry.Title}}
{%- endfor %}

""",
    }


def lint_dates():
    c = Collection().shelves(["read"])
    return {
        'title': 'Finished before starting',
        'df': c.df[c.df.Read < c.df.Started],
        'template': """
{%- for entry in df.itertuples() %}
{{entry.Author}}, {{entry.Title}}: {{entry.Started.date()}} - {{entry.Read.date()}}
{%- endfor %}

""",
    }


def lint_missing_language():
    c = Collection()
    return {
        'title': 'Missing a language',
        'df': c.df[c.df.Language.isnull()],
        'template': """
{%- for entry in df.itertuples() %}
{{entry.Author}}, {{entry.Title}} https://www.goodreads.com/book/show/{{entry.Index}}
{%- endfor %}

""",
    }


def lint_scheduled_misshelved():
    c = Collection().shelves(["read", "currently-reading", "to-read"])
    return {
        'title': 'Scheduled books on wrong shelves',
        'df': c.df[c.df.Scheduled.notnull()],
        'template': """
{%- for entry in df.itertuples() %}
{{entry.Author}}, {{entry.Title}}
    {{entry.Shelf}}
{%- endfor %}

""",
    }


# scheduled books by authors i've already read this year
def lint_overscheduled():
    c = Collection(merge=True)
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
        "title": "Multiple scheduled books by the same author",
        "df": df,
        "template": """
{%- for entry in df.itertuples() %}
{{entry.Author}}, {{entry.Title}}
{%- endfor %}

""",
    }


def lint_scheduling():
    c = Collection()

    df = c.df

    from reading.scheduling import _set_schedules
    import datetime

    horizon = datetime.date.today().year + 3

    _set_schedules(df, config('scheduled'), col='Expected')

    df = df[df.Expected.notnull()]  # only automatically scheduled
    df = df[df.Expected.dt.year < horizon]
    df = df[df.Scheduled.dt.year != df.Expected.dt.year]

    return {
        'title': 'Mis-scheduled books',
        'df': df,
        'template': """
{%- for entry in df.itertuples() %}
{{entry.Author}}, {{entry.Title}}:  {{entry.Expected.year}}, not {{entry.Scheduled.year}}
  https://www.goodreads.com/book/show/{{entry.Index}}
{%- endfor %}

""",
    }


def lint_duplicates():
    df = Collection(merge=True).df

    # FIXME move this into the Collection and make it non-manky
    df = df.groupby('Work').filter(lambda x: len(x) > 1)
    df = df.groupby('Work').aggregate({
        'Author': 'first',
        'Title': 'first',
        'Work': 'first',
        'Shelf': lambda x: ', '.join(list(x)),
    })
    df = df.groupby('Work').filter(lambda x: x.Shelf != 'ebooks, kindle')

    return {
        'title': 'Duplicate books',
        'df': df,
        'template': """
{%- for entry in df.itertuples() %}
{{entry.Author}}, {{entry.Title}}
    {{entry.Shelf}}
{%- endfor %}

""",
    }


# books in dubious formats
def lint_binding():
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
    c = Collection().shelves(exclude=["kindle"])
    return {
        'title': 'Bad binding',
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


def lint_author_metadata():
    df = Collection().shelves(["read"]).df  # FIXME

    return {
        'title': 'Missing author metadata',
        'df': df[df[['Nationality', 'Gender']].isnull().any(axis='columns')],
        'template': """
{%- for entry in df.itertuples() %}
{{entry.Author}}, {{entry.Title}}
{%- endfor %}

""",
    }


# books on elsewhere shelf that are not marked as borrowed.
def lint_missing_borrowed():
    c = Collection().shelves(["elsewhere", "library"]).borrowed(False)
    return {
        'title': 'Elsewhere but not marked as borrowed',
        'df': c.df,
        'template': """
{%- for entry in df.itertuples() %}
{{entry.Author}}, {{entry.Title}}
{%- endfor %}

""",
    }


# books on elsewhere shelf that are not marked as borrowed.
def lint_extraneous_borrowed():
    c = Collection().shelves(["to-read"]).borrowed(True)
    return {
        'title': 'To-read but marked as borrowed',
        'df': c.df,
        'template': """
{%- for entry in df.itertuples() %}
{{entry.Author}}, {{entry.Title}}
{%- endfor %}

""",
    }


# books i've borrowed that need to be returned.
def lint_needs_returning():
    c = Collection().shelves(["read"]).borrowed(True)
    return {
        'title': 'Borrowed books to return',
        'df': c.df,
        'template': """
{%- for entry in df.itertuples() %}
{{entry.Author}}, {{entry.Title}}
{%- endfor %}

""",
    }


def lint_not_rated():
    c = Collection().shelves(["read"])
    return {
        "title": "Read but not yet rated",
        "df": c.df[c.df.Rating == 0],
        "template": """
{%- for entry in df.itertuples() %}
{{entry.Author}}, {{entry.Title}}, https://www.goodreads.com/review/edit/{{entry.Index}}
{%- endfor %}

""",
    }


# find unnecessary fixes
# FIXME update
def lint_fixes():
    c = Collection(fixes=None)

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
        'title': 'Fixes',
        'df': errors,
        'template': """
{%- for entry in df %}
{{entry}}
{%- endfor %}

"""
    }


################################################################################

def main(args):
    # run them all
    n = __import__(__name__)
    for f in [x for x in dir(n.lint) if x.startswith('lint_')]:
        if args.pattern and args.pattern not in f:
            continue

        report = getattr(n.lint, f)()

        # FIXME
        if report is None or 'df' not in report:
            print(report)
            continue

        if not len(report['df']):
            continue

        print('=== {} ==='.format(report['title']))
        from jinja2 import Template

        if 'template' not in report:
            continue

        print(Template(report['template']).render(df=report['df']))

