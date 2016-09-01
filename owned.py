#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import datetime

import pandas as pd

GR_HISTORY = 'data/goodreads_library_export.csv'


def get_books(filename):
    df = pd.read_csv(filename, index_col=0)

    for column in ['Date Read', 'Date Added']:
        df[column] = pd.to_datetime(df[column])
    # this doesn't seem to be set for some reason
    df['Bookshelves'].fillna('read', inplace=True)

    columns = [
        'Title',
        'Author',
        'Exclusive Shelf',
    ]

    return df[columns].sort_index()


df = get_books(GR_HISTORY)

owned_shelves = [
    'pending',
    'elsewhere',
]

owned = df[df['Exclusive Shelf'].isin(owned_shelves)].sort(['Author', 'Title'])


author = None

for ix, row in owned.iterrows():
    if author != row['Author']:
        author = row['Author']
        print
        print row['Author']

    print '* {Title}'.format(**row.to_dict())

