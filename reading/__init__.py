# -*- coding: utf-8 -*-

import sys
import yaml
import pandas as pd

import reading.ebooks


GR_HISTORY = 'data/goodreads_library_export.csv'


################################################################################

def get_books(shelves=None, categories=None, languages=None, no_fixes=False, fix_names=True):
    df = pd.concat([
        get_gr_books(),
        reading.ebooks.get_books(),
    ])

    # filtering
    if categories:
        df = df[df.Category.isin(categories)]
    else:
        # ignore articles unless explicitly requested
        df = df[~df.Category.isin(['articles'])]

    if languages:
        df = df[df['Language'].isin(languages)]
    if shelves:
        df = df[df['Exclusive Shelf'].isin(shelves)]

    return df


# load the data and patch it up
def get_gr_books(filename=GR_HISTORY, no_fixes=False, fix_names=True):
    try:
        df = pd.read_csv(filename, index_col=0)
    except IOError:
        print("Missing file: '{}'".format(filename))
        sys.exit()

    # split the volume number and series name/number out from the title
    s = df['Title'].str.extract('(?P<Title>.+?)(?: (?P<Volume>I+))?(?: ?\((?P<Series>.+?),? +#(?P<Entry>\d+)(?:; .+?)?\))?$', expand=True)
    df = df.rename(columns={
        'Title': 'Original Title',
    }).join(s)

    # lint doesn't want the fixes applying.
    if not no_fixes:
        with open('data/fixes.yml') as fh:
            df.update(pd.DataFrame(yaml.load(fh)).set_index(['Book Id']))

    for column in ['Date Read', 'Date Added']:
        df[column] = pd.to_datetime(df[column])

    # remove old read books
    df = df[~((df['Exclusive Shelf'] == 'read')&(df['Date Read'] < '2016'))]

    # this doesn't seem to be set for some reason
    df['Bookshelves'].fillna('read', inplace=True)

    # the year it's scheduled for (if any)
    df['Scheduled'] = df['Bookshelves'].str.extract(r'\b(\d{4})\b', expand=True)

    df['grid'] = df.index

    # remove columns that just aren't interesting.
    df = df.drop([
        'Additional Authors',
        'Author l-f',
        'Bookshelves with positions',
        'ISBN',
        'ISBN13',
        'My Review',
        'Owned Copies',
        'Publisher',
        'Year Published'
    ], axis=1)

    return df.dropna(axis='columns', how='all')


# vim: ts=4 : sw=4 : et
