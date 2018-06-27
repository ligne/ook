#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import datetime
import yaml
import pandas as pd

import reading
from reading.collection import Collection


# TODO check there aren't any unwanted entries in fixes.yml

today = datetime.date.today()


def print_entries(df, desc, additional=[]):
    if not len(df):
        return

    fmt = "{Author}, '{Title}'"
    for field in additional:
        fmt += '\n  {0}:\t{{{0}}}'.format(field)

    print('=== {} ==='.format(desc))
    print()
    for ix, row in df.iterrows():
        print(fmt.format(**row))
        print()


################################################################################

def lint_missing_pagecount():
    c = Collection(fixes=None)
    return c.df[c.df.Pages.isnull()]


def lint_missing_published_date():
    c = Collection(shelves=['pending', 'ebooks', 'elsewhere', 'read'])
    return c.df[c.df.Published.isnull()]


def lint_scheduled_misshelved():
    c = Collection(shelves=['read', 'currently-reading', 'to-read'])
    return c.df[c.df.Scheduled.notnull()]


# FIXME no longer possible.
## check for books in multiple years
#def check_duplicate_years(df):
#    duplicate_years = reading.on_shelves(df, others=[r'\d{4}.+?\d{4}'])
#    print_entries(duplicate_years, 'Books in multiple years', ['Bookshelves'])


# scheduled books by authors i've already read this year
def check_scheduled_but_already_read(df):
    ignore_authors = [
        'Terry Pratchett',
    ]

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


# duplicate books
def check_duplicate_books(df):
    # FIXME may still want this to remove any stray descriptions?
#     df['Clean Title'] = df['Title'].str.replace(r' \(.+?\)$', '')

    # duplicates here are expected.
    df = df[~(df['Exclusive Shelf'].isin(['ebooks', 'currently-reading']))]

    # ignore books that i've got scheduled
    # FIXME only if one is on Kindle?
    df = df[df.Scheduled.isnull()]

    # FIXME case-insensitive?
    df = df[df.duplicated(subset=['Title', 'Author', 'Volume'])]
    print_entries(df, 'Duplicate books')


# books in dubious formats
def lint_binding():
    good_bindings = [
        'Paperback',
        'Hardcover',
        'Mass Market Paperback',
        'Kindle Edition',
        'ebook',
        'Poche',
    ]
    c = Collection(shelves=[
        'read',
        'currently-reading',
        'pending',
        'elsewhere',
        'library',
        'ebooks',
#        'to-read',
    ])
    return c.df[~c.df.Binding.isin(good_bindings)]


def check_read_author_metadata(df):
    df = reading.read_since(df, '2016')
    df = df[df[['Nationality', 'Gender']].isnull().any(axis='columns')]
    print_entries(df, 'Missing author metadata', ['Nationality', 'Gender'])


# books on elsewhere shelf that are not marked as borrowed.
def lint_missing_borrowed():
    c = Collection(shelves=['elsewhere'], borrowed=False)
    return c.df


# books i've borrowed that need to be returned.
def lint_needs_returning():
    c = Collection(shelves=['read'], borrowed=True)
    return c.df


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
n = __import__(__name__)
for f in [x for x in dir(n) if x.startswith('check_')]:
    func = getattr(n, f)
    # FIXME push this down into the funtions
    doc = func.__doc__
    if doc and doc == 'no_fixes':
        df = reading.get_books(no_fixes=True)
    else:
        df = reading.get_books()

    func(df)

print('='*80)
print()

for f in [x for x in dir(n) if x.startswith('lint_')]:
    print(getattr(n, f)())


# vim: ts=4 : sw=4 : et
