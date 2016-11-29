#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import datetime

import pandas as pd

import reading

# FIXME also books that i want to buy. and books that i have ebooks of?

df = reading.get_books()

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

