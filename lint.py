#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

import pandas as pd

GR_HISTORY = 'data/goodreads_library_export.csv'

df = pd.read_csv(GR_HISTORY).sort('Date Added')
df = df.set_index(pd.to_datetime(df['Date Added']))


# this doesn't seem to be set for some reason
df['Bookshelves'].fillna('read', inplace=True)

pd.set_option('display.max_rows', 999, 'display.width', 1000)

# missing page count
print '=== Missing page count ==='
pending = df.ix['2016':][['Title', 'Author', 'Number of Pages']]
print pending[pending.isnull().any(axis=1)][['Title', 'Author']]
print


# check for $year/currently-reading double-counting
f = df[df['Bookshelves'].str.contains(r'\b\d+\b', na=False)]
f = f[~f['Exclusive Shelf'].isin(['pending', 'ebooks', 'elsewhere'])][['Title', 'Author']]
if len(f):
    print "=== Scheduled books on the wrong shelf ==="
    print f
    print


# check for books in multiple years
duplicate_years = df[df['Bookshelves'].str.contains(r'\d{4}.+?\d{4}')]
if len(duplicate_years):
    print '=== Books in multiple years ==='
    print duplicate_years[['Title', 'Author', 'Bookshelves']]
    print


# scheduled books by authors i've already read this year
import suggestions
authors = suggestions.already_read(suggestions.get_books())
f = df[df['Bookshelves'].str.contains(r'\b2016\b', na=False)]
duplicate_authors = f[f['Author'].isin(authors)][['Title', 'Author']]
if len(duplicate_authors):
    print '=== Multiple scheduled books by the same author ==='
    print duplicate_authors[['Title', 'Author']]
    print


# duplicate books
duplicate_books = df.copy()
duplicate_books['Clean Title'] = duplicate_books['Title'].str.replace(r' \(.+?\)$', '')
duplicate_books = duplicate_books[duplicate_books.duplicated(subset=['Clean Title', 'Author'])]
if len(duplicate_books):
    print '=== Duplicate books ==='
    print duplicate_books[['Clean Title', 'Author']]
    print


# books with silly formats
good_bindings = [
    'Paperback',
    'Hardcover',
    'Mass Market Paperback',
]
# ignore old books, along with those that i've not properly entered.
binding = df[~df['Exclusive Shelf'].isin(['read', 'to-read', 'elsewhere'])]
bad_binding = binding[(~binding['Binding'].isin(good_bindings))&(~binding['Binding'].isnull())][['Title', 'Author', 'Binding']]
if len(bad_binding):
    print '=== Bad format ==='
    print bad_binding[['Title', 'Author', 'Binding']]
    print

