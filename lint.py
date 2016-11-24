#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import datetime
import yaml

import suggestions
import reading

import pandas as pd


today = datetime.date.today()

pd.set_option('display.max_rows', 999, 'display.width', 1000)


def print_entries(df, desc, additional=None):
    if not len(df):
        return

    fmt = "{Author}, '{Title}'"
    if additional:
        fmt += ':\n'
        fmt += '\t{' + additional[0] + '}\n'

    print '=== {} ==='.format(desc)
    print
    for ix, row in df.iterrows():
        print fmt.format(**row)


################################################################################

# missing page count
def check_missing_page_count():
    df = reading.get_books(no_fixes=True)
    df = df[df['Date Added'].dt.year >= 2016][['Title', 'Author', 'Number of Pages']]
    missing = df[df.isnull().any(axis=1)]
    print_entries(missing, 'Missing page count')


# i've not manually added the start date
def check_missing_start_date():
    df = reading.get_books()
    df = df[df['Date Read'].dt.year >= 2016]
    missing_start = df[df['Date Started'].isnull()]
    print_entries(missing_start, 'Missing a start date')


# check for $year/currently-reading double-counting
def check_scheduled_book_on_wrong_shelf():
    df = reading.get_books()
    f = df[df['Bookshelves'].str.contains(r'\b\d+\b')]
    f = f[~f['Exclusive Shelf'].isin(['pending', 'ebooks', 'elsewhere'])]
    print_entries(f, 'Scheduled books on the wrong shelf', ['Bookshelves'])


# check for books in multiple years
def check_duplicate_years():
    df = reading.get_books()
    duplicate_years = df[df['Bookshelves'].str.contains(r'\d{4}.+?\d{4}')]
    print_entries(duplicate_years, 'Books in multiple years', ['Bookshelves'])


# scheduled books by authors i've already read this year
# FIXME should be clearer...
def check_scheduled_but_already_read():
    df = reading.get_books()
    ignore_authors = [
        'Terry Pratchett',
    ]
    authors = suggestions.already_read(df)
    pattern = r'\b{}\b'.format(today.year)
    df = df[df['Bookshelves'].str.contains(pattern)]
    df = df[(df['Author'].isin(authors))&(~df['Author'].isin(ignore_authors))]
    print_entries(df, 'Multiple scheduled books by the same author')


# duplicate books
# FIXME should be clearer...
def check_duplicate_books():
    duplicate_books = reading.get_books()
    duplicate_books['Clean Title'] = duplicate_books['Title'].str.replace(r' \(.+?\)$', '')
    duplicate_books = duplicate_books[duplicate_books.duplicated(subset=['Clean Title', 'Author'])]
    print_entries(duplicate_books, 'Duplicate books')


# books with silly formats
def check_bad_binding():
    df = reading.get_books()
    good_bindings = [
        'Paperback',
        'Hardcover',
        'Mass Market Paperback',
        'Kindle Edition',
    ]
    # ignore old books, along with those that i've not properly entered.
    binding = df[~df['Exclusive Shelf'].isin(['read', 'to-read', 'elsewhere'])]
    bad_binding = binding[(~binding['Binding'].isin(good_bindings))&(~binding['Binding'].isnull())]
    print_entries(bad_binding, 'Bad binding', ['Binding'])


# run them all
n = __import__(__name__)
for f in [ x for x in dir(n) if x.startswith('check_') ]:
    getattr(n, f)()

