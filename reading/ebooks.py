# -*- coding: utf-8 -*-

import sys
import glob

import pandas as pd

from reading.author import Author


# FIXME get additional data: clean title, original publication date
# FIXME drop entries that already exist on ebooks shelf?
def get_books(fix_names=True):
        df = pd.read_csv('data/wordcounts-oldform.csv', sep='\t', index_col=False)

        df.loc[:,'Author'].fillna('', inplace=True)

        df['Subtitle'] = df.Title.str.split(' / ', 1).str.get(1)
        df['Title'] = df.Title.str.split(' / ', 1).str.get(0)

        df['Number of Pages'] = (df.Words / 390)

        df['Exclusive Shelf'] = 'kindle'
        df['Bookshelves'] = 'kindle'
        df['Binding'] = 'ebook'

        for col in df.columns:
            if col[0].islower(): del df[col]

        # set a new index that won't clash with the GR one.
        return df.set_index([['_' + str(x) for x in range(len(df.index))]])


# vim: ts=4 : sw=4 : et
