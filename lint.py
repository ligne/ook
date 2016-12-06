#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import datetime
import yaml

import suggestions
import reading

import pandas as pd


# TODO check there aren't any unwanted entries in fixes.yml

today = datetime.date.today()


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
    missing = df[df.isnull()['Number of Pages']]
    print_entries(missing, 'Missing page count')


# i've not manually added the start date
def check_missing_start_date():
    df = reading.get_books()
    df = reading.read_since(df, 2016)
    missing_start = df[df['Date Started'].isnull()]
    print_entries(missing_start, 'Missing a start date')


# the original publication year is missing
def check_missing_publication_year():
    df = reading.get_books()
    df = df[df['Original Publication Year'].isnull()]
    print_entries(df, 'Missing a publication year')


# check for $year/currently-reading double-counting
def check_scheduled_book_on_wrong_shelf():
    df = reading.get_books()
    f = df[df.Scheduled.notnull() & ~df['Exclusive Shelf'].isin(['pending', 'ebooks', 'elsewhere'])]
    print_entries(f, 'Scheduled books on the wrong shelf', ['Bookshelves'])


# check for books in multiple years
def check_duplicate_years():
    df = reading.get_books()
    duplicate_years = reading.on_shelves(df, others=[r'\d{4}.+?\d{4}'])
    print_entries(duplicate_years, 'Books in multiple years', ['Bookshelves'])


# scheduled books by authors i've already read this year
def check_scheduled_but_already_read():
    df = reading.get_books()

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
# FIXME should be clearer...
def check_duplicate_books():
    df = reading.get_books()
    # FIXME may still want this to remove any stray descriptions?
#     df['Clean Title'] = df['Title'].str.replace(r' \(.+?\)$', '')
    df = df[df.duplicated(subset=['Title', 'Author', 'Volume'])]
    print_entries(df, 'Duplicate books')


# books with silly formats
def check_bad_binding():
    df = reading.get_books()
    good_bindings = [
        'Paperback',
        'Hardcover',
        'Mass Market Paperback',
        'Kindle Edition',
        'ebook',
    ]
    # ignore old books, along with those that i've not properly entered.
    binding = df[~df['Exclusive Shelf'].isin(['read', 'to-read', 'elsewhere'])]
    bad_binding = binding[(~binding['Binding'].isin(good_bindings))&(~binding['Binding'].isnull())]
    print_entries(bad_binding, 'Bad binding', ['Binding'])


# run them all
n = __import__(__name__)
for f in [x for x in dir(n) if x.startswith('check_')]:
    getattr(n, f)()

