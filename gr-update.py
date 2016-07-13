#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import datetime

import suggestions

import pandas as pd

GR_HISTORY = 'data/goodreads_library_export.csv'


def get_books(filename):
    df = pd.read_csv(filename, index_col=0)
    for column in ['Date Read', 'Date Added']:
        df[column] = pd.to_datetime(df[column])
    # this doesn't seem to be set for some reason
    df['Bookshelves'].fillna('read', inplace=True)

    #print df.columns

    columns = [
        'Title',
        'Author',
        'Date Added',
        'Bookshelves',
        'Exclusive Shelf',
    ]

    return df[columns].sort_index()


df1 = get_books(GR_HISTORY)
df2 = get_books(sys.argv[1])

# force both to use the same index
ix = df1.index|df2.index
df1 = df1.reindex(ix)
df2 = df2.reindex(ix)

ne_stacked = (df1 != df2).stack()
changed = ne_stacked[ne_stacked]

for (index, _df) in changed.groupby(level=0):
    if df1.ix[index].isnull().any():
        print "Removed", df2.ix[index].to_dict()['Title']
    elif df2.ix[index].isnull().any():
        print "Added", df1.ix[index].to_dict()['Title']
    else:
        row = df1.ix[index].to_dict()
        print '{Author}, {Title}'.format(**row)

        for col in _df.index.get_level_values(1).values:
            if col == 'Bookshelves':
                old = set(df2.ix[index][col].split(', '))
                new = set(df1.ix[index][col].split(', '))
                added = new - old
                removed = old - new
                print '{}:'.format(col)
                if removed:
                    print '\t-{}'.format(', -'.join(removed)),
                if added:
                    print '\t+{}'.format(', -'.join(added)),
                print
            else:
                print '{}:\n\t{} -> {}'.format(col, df2.ix[index][col], df1.ix[index][col])

    print '----'


    # FIXME handle books where the title has changed?

