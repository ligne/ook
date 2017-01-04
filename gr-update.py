#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import datetime

import pandas as pd

import reading

columns = [
    'Title',
    'Author',
    'Date Added',
    'Bookshelves',
    'Exclusive Shelf',
    'Series',
    'Entry',
    'Original Publication Year',
]


def compare(df_old, df_new):
    df_old = df_old[columns]
    df_new = df_new[columns]


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
                        print '  -{}'.format(', -'.join(removed)),
                    if added:
                        print '  +{}'.format(', +'.join(added)),
                    print
                else:
                    print '{}:\n  {} -> {}'.format(col, old_row[col], new_row[col])

        print
        print '----'


if __name__ == "__main__":
    compare(
        reading.get_books(no_fixes=True),
        reading.get_books(no_fixes=True, filename=sys.argv[1]),
    )


# vim: ts=4 : sw=4 : et
