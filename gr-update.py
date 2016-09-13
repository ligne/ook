#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import datetime

import pandas as pd

GR_HISTORY = 'data/goodreads_library_export.csv'


def get_books(filename):
    try:
        df = pd.read_csv(filename, index_col=0)
    except IOError:
        print "Missing file: '{}'".format(filename)
        sys.exit()

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

for (index, changes) in changed.groupby(level=0):
    old_row = df_old.ix[index]
    new_row = df_new.ix[index]

    if new_row.isnull().any():
        print "Removed {Title} by {Author}".format(**old_row)
    elif old_row.isnull().any():
        print "Added {Title} by {Author}".format(**new_row)
        # also show any bookshelves it's been added to
        new = set(new_row['Bookshelves'].split(', '))
        added = new - set([new_row['Exclusive Shelf']])
        if added:
            print 'Bookshelves:'
            print '\t+{}'.format(', +'.join(added))
    else:
        print '{Author}, {Title}'.format(**old_row)

        for col in changes.index.get_level_values(1).values:
            if col == 'Bookshelves':
                old = set(old_row[col].split(', '))
                new = set(new_row[col].split(', '))

                added   = new - old - set([new_row['Exclusive Shelf']])
                removed = old - new - set([old_row['Exclusive Shelf']])

                if not (added or removed):
                    continue

                print '{}:'.format(col)
                if removed:
                    print '\t-{}'.format(', -'.join(removed)),
                if added:
                    print '\t+{}'.format(', +'.join(added)),
                print
            else:
                print '{}:\n\t{} -> {}'.format(col, old_row[col], new_row[col])

    print '----'

