#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import datetime

import pandas as pd

import reading

# FIXME also books that i want to buy. and books that i have ebooks of?

df = reading.get_books(shelves=[
    'pending',
    'elsewhere',
])

# deduplicate multiple volumes
df = df.drop_duplicates(['Author', 'Title'])

g = df.sort_values(['Author', 'Title']).groupby('Author')

for author in sorted(g.groups.keys()):
    print('{}'.format(author))
    for ix, row in g.get_group(author).iterrows():
        print('* {Title}'.format(**row))
    print()

print('----')
print('Ebooks')

df = reading.get_books(shelves=[
    'kindle',
])

# deduplicate multiple volumes
df = df.drop_duplicates(['Author', 'Title'])

g = df.sort_values(['Author', 'Title']).groupby('Author')

for author in sorted(g.groups.keys()):
    print('{}'.format(author))
    for ix, row in g.get_group(author).iterrows():
        print('* {Title}'.format(**row))
    print()

print('----')
print('To read')

df = reading.get_books(shelves=[
    'to-read',
])

# deduplicate multiple volumes
df = df.drop_duplicates(['Author', 'Title'])

g = df.sort_values(['Author', 'Title']).groupby('Author')

for author in sorted(g.groups.keys()):
    print('{}'.format(author))
    for ix, row in g.get_group(author).iterrows():
        print('* {Title}'.format(**row))
    print()

# vim: ts=4 : sw=4 : et
