#!/usr/bin/python3
# -*- coding: utf-8 -*-

import datetime
import yaml
import pandas as pd

import reading
from reading.collection import Collection


def lint_missing_pagecount():
    c = Collection(fixes=None)
    return {
        'title': 'Missing a pagecount',
        'df': c.df[c.df.Pages.isnull()],
        'template': """
{%- for entry in df.itertuples() %}
{{entry.Author}}, {{entry.Title}}
{%- endfor %}

""",
    }


def lint_missing_category():
    c = Collection(fixes=None)
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
    c = Collection(shelves=['pending', 'ebooks', 'elsewhere', 'read'])
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
    c = Collection(shelves=['read'])
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
    c = Collection(shelves=['read', 'currently-reading', 'to-read'])
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
# FIXME rewrite this too
def check_scheduled_but_already_read(df):
    ignore_authors = [
        'Terry Pratchett',
        'Iain Banks',
    ]

    today = datetime.date.today()

    # has been scheduled
    scheduled = df.Scheduled.notnull()
    # duplicate author for the same year, ignoring volumes of the same book
    duplicated = df.duplicated(['Author', 'Scheduled', 'Volume'])
    # by authors i expect to be reading several times a year
    ignored = df['Author'].isin(ignore_authors)
    # scheduled for this year
    this_year = df.Scheduled == str(today.year)
    # by authors i've already read this year
    authors = df[(df['Date Read'].dt.year == today.year) | (df['Exclusive Shelf'] == 'currently-reading')].Author.values
    read_this_year = df.Author.isin(authors)

    df = df[scheduled & ~ignored & (duplicated | (this_year & read_this_year))]
    print_entries(df, 'Multiple scheduled books by the same author', ['Scheduled'])


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
        'Hardcover',
        'Mass Market Paperback',
        'Kindle Edition',
        'ebook',
        'Poche',
        'Broché',
        'Relié',
        'Board book',
    ]
    c = Collection(shelves=[
        'read',
        'currently-reading',
        'pending',
        'elsewhere',
        'library',
        'ebooks',
        'to-read',
    ])
    return {
        'title': 'Bad binding',
        'df': c.df[~(c.df.Binding.isin(good_bindings)|c.df.Binding.isnull())],
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
    df = Collection(shelves=['read']).df  # FIXME

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
    c = Collection(shelves=['elsewhere', 'library'], borrowed=False)
    return {
        'title': 'Elsewhere but not marked as borrowed',
        'df': c.df,
        'template': """
{%- for entry in df.itertuples() %}
{{entry.Author}}, {{entry.Title}}
{%- endfor %}

""",
    }


# books i've borrowed that need to be returned.
def lint_needs_returning():
    c = Collection(shelves=['read'], borrowed=True)
    return {
        'title': 'Borrowed books to return',
        'df': c.df,
        'template': """
{%- for entry in df.itertuples() %}
{{entry.Author}}, {{entry.Title}}
{%- endfor %}

""",
    }


# find unnecessary fixes
def lint_fixes():
    c = Collection(fixes=None)

    with open('data/fixes.yml') as fh:
        fixes = yaml.load(fh)

    for f in fixes:
        book = f['Book Id']
        if book not in c.df.index:
            print('{} does not exist'.format(book))
            continue

        for k,v in f.items():
            if k == 'Book Id':
                continue
            elif k in ['Date Added', 'Date Started', 'Date Read']:
                k = k[5:]
                v = pd.Timestamp(v)
            elif k =='Original Publication Year':
                k = 'Published'
            elif k == 'Entry':
                v = format(v, '.0f')
            elif k not in c.df.columns:
                print('!!!', k)
                continue

            if c.df.loc[book,k] == v:
                print("Unnecessary entry [{},{}]".format(book, k))

    return


################################################################################

# run them all
for f in [x for x in dir(n) if x.startswith('lint_')]:
    report = getattr(n, f)()

    # FIXME
    if report is None or not 'df' in report:
        print(report)
        continue

    if not len(report['df']):
        continue

    print('=== {} ==='.format(report['title']))
    from jinja2 import Template

    if not 'template' in report:
        continue

    print(Template(report['template']).render(df=report['df'].sort_values(['Author', 'Title'])))


# vim: ts=4 : sw=4 : et
