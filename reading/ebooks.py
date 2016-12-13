# -*- coding: utf-8 -*-

import sys
import glob

import pandas as pd

from reading.author import Author


# FIXME get additional data: clean title, original publication date
# FIXME drop entries that already exist on ebooks shelf?
def get_books(fix_names=True):
        df = pd.read_csv('data/wordcounts.csv', sep='\t', index_col=False)

        df = df[~(df.category == 'articles')]

        df = df.dropna(subset=['Author'])

        df['Number of Pages'] = (df.words / 390).astype(int)

        df['Exclusive Shelf'] = 'kindle'
        df['Bookshelves'] = 'kindle'
        df['Binding'] = 'ebook'

        # standardise the author name.  FIXME use the QID instead?
        if fix_names:
            df['Author'] = df['Author'].apply(lambda x: Author(x).get('Name', x))

        for col in ['Gender', 'Nationality']:
            df[col] = df['Author'].apply(lambda x: Author(x).get(col))

        for col in df.columns:
            if col[0].islower(): del df[col]

        # set a new index that won't clash with the GR one.
        return df.set_index([['_' + str(x) for x in range(len(df.index))]])


# vim: ts=4 : sw=4 : et
