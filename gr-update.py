#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import datetime

import pandas as pd

import reading


def get_books(*args):
    df = reading.get_books(no_fixes=True, *args)

    columns = [
        'Title',
        'Author',
        'Date Added',
        'Bookshelves',
        'Exclusive Shelf',
        'Series',
        'Entry',
    ]

    return df[columns].sort_index()


df_old = get_books()
df_new = get_books(sys.argv[1])

# force both to use the same index
ix = df_old.index | df_new.index
df_old = df_old.reindex(ix).fillna('')
df_new = df_new.reindex(ix).fillna('')

ne_stacked = (df_old != df_new).stack()
changed = ne_stacked[ne_stacked]

for (index, changes) in changed.groupby(level=0):
    old_row = df_old.ix[index]
    new_row = df_new.ix[index]

    if not new_row['Author']:
        print "Removed '{Title}' by {Author}".format(**old_row)
        print '  Bookshelves: {Bookshelves}'.format(**old_row)
    elif not old_row['Author']:
        fmt = "Added '{Title}' by {Author}"
        if new_row['Series']:
            fmt += ' ({Series}, book {Entry})'
        print fmt.format(**new_row)
        # also show any bookshelves it's been added to
        print '  Bookshelves: {Bookshelves}'.format(**new_row)
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

# vim: ts=4 : sw=4 : et
