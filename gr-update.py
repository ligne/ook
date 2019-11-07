#!/usr/bin/python3
# -*- coding: utf-8 -*-

import argparse

import reading.goodreads
from reading.compare import compare
from reading.collection import Collection


parser = argparse.ArgumentParser()
parser.add_argument('-n', '--ignore-changes', action='store_true')
args = parser.parse_args()

df = reading.goodreads.get_books()

# FIXME shortcut for this, please!
old = Collection(shelves=[
    'read',
    'currently-reading',
    'pending',
    'elsewhere',
    'library',
    'ebooks',
    'to-read',
], fixes=False)

if not args.ignore_changes:
    df.sort_index().to_csv('data/goodreads.csv', float_format='%g')

compare(old.df, df)

# vim: ts=4 : sw=4 : et
