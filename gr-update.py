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
        'Date Added',
        'Bookshelves',
        'Exclusive Shelf',
    ]

    return df[columns].sort_index()


df_old = get_books(GR_HISTORY)
df_new = get_books(sys.argv[1])

# force both to use the same index
ix = df_old.index|df_new.index
df_old = df_old.reindex(ix)
df_new = df_new.reindex(ix)

ne_stacked = (df_old != df_new).stack()
changed = ne_stacked[ne_stacked]

for (index, _df) in changed.groupby(level=0):
    if df_old.ix[index].isnull().any():
        print "Removed", df_new.ix[index].to_dict()['Title']
    elif df_new.ix[index].isnull().any():
        print "Added", df_old.ix[index].to_dict()['Title']
    else:
        row = df_old.ix[index].to_dict()
        print '{Author}, {Title}'.format(**row)

        for col in _df.index.get_level_values(1).values:
            if col == 'Bookshelves':
                old = set(df_new.ix[index][col].split(', '))
                new = set(df_old.ix[index][col].split(', '))
                added = new - old
                removed = old - new
                print '{}:'.format(col)
                if removed:
                    print '\t-{}'.format(', -'.join(removed)),
                if added:
                    print '\t+{}'.format(', -'.join(added)),
                print
            else:
                print '{}:\n\t{} -> {}'.format(col, df_new.ix[index][col], df_old.ix[index][col])

    print '----'


    # FIXME handle books where the title has changed?

