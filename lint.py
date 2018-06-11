#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import datetime
import yaml

import reading

import pandas as pd


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

# missing page count
def check_missing_page_count(df):
    '''no_fixes'''
    df = reading.on_shelves(df, ['pending', 'ebooks'])
    missing = df[df.isnull()['Number of Pages']]
    print_entries(missing, 'Missing page count')


# i've not manually added the start date
def check_missing_start_date(df):
    df = reading.read_since(df, 2016)
    missing_start = df[df['Date Started'].isnull()]
    print_entries(missing_start, 'Missing a start date')


# the original publication year is missing
def check_missing_publication_year(df):
    # FIXME
    df = reading.on_shelves(df, ['pending', 'ebooks', 'elsewhere'])
    df = df[df['Original Publication Year'].isnull()]
    print_entries(df, 'Missing a publication year')


# check for $year/currently-reading double-counting
def check_scheduled_book_on_wrong_shelf(df):
    f = df[df.Scheduled.notnull() & ~df['Exclusive Shelf'].isin(['pending', 'ebooks', 'elsewhere'])]
    print_entries(f, 'Scheduled books on the wrong shelf', ['Bookshelves'])


# check for books in multiple years
def check_duplicate_years(df):
    duplicate_years = reading.on_shelves(df, others=[r'\d{4}.+?\d{4}'])
    print_entries(duplicate_years, 'Books in multiple years', ['Bookshelves'])


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


# books with silly formats
def check_bad_binding(df):
    good_bindings = [
        'Paperback',
        'Hardcover',
        'Mass Market Paperback',
        'Kindle Edition',
        'ebook',
        'Poche',
    ]
    # ignore old books, along with those that i've not properly entered.
    binding = df[~df['Exclusive Shelf'].isin(['read', 'to-read', 'elsewhere'])]
    bad_binding = binding[(~binding['Binding'].isin(good_bindings))&(~binding['Binding'].isnull())]
    print_entries(bad_binding, 'Bad binding', ['Binding'])


def check_read_author_metadata(df):
    df = reading.read_since(df, '2016')
    df = df[df[['Nationality', 'Gender']].isnull().any(axis='columns')]
    print_entries(df, 'Missing author metadata', ['Nationality', 'Gender'])


# books on elsewhere shelf that are not marked as borrowed.
def check_missing_borrowed(df):
    df = reading.on_shelves(df, ['elsewhere'])

    shelf = 'borrowed'
    df = df[~df['Bookshelves'].str.contains(r'\b{}\b'.format(shelf))]

    print_entries(df, 'Elsewhere but not marked as borrowed')


# books i've borrowed that need to be returned.
def check_to_be_returned(df):
    df = reading.on_shelves(df, ['read'], ['borrowed'])
    print_entries(df, 'Borrowed and need to be returned')


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

# vim: ts=4 : sw=4 : et
