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

g = reading.on_shelves(df, owned_shelves).sort(['Author', 'Title']).groupby('Author')

for author in sorted(g.groups.keys()):
    print '{}'.format(author)
    for ix, row in g.get_group(author).iterrows():
        print '* {Title}'.format(**row)
    print

# vim: ts=4 : sw=4 : et
