# -*- coding: utf-8 -*-

import sys
import yaml

import pandas as pd


GR_HISTORY = 'data/goodreads_library_export.csv'


################################################################################

# load the data and patch it up
def get_books(filename=GR_HISTORY, no_fixes=False):
    try:
        df = pd.read_csv(filename, index_col=0)
    except IOError:
        print "Missing file: '{}'".format(filename)
        sys.exit()

    # lint doesn't want the fixes applying.
    if not no_fixes:
        with open('data/fixes.yml') as fh:
            df.update(pd.DataFrame(yaml.load(fh)).set_index(['Book Id']))

    with open('data/started.yml') as fh:
        df['Date Started'] = pd.DataFrame(yaml.load(fh)).set_index(['Book Id'])

    for column in ['Date Read', 'Date Added', 'Date Started']:
        df[column] = pd.to_datetime(df[column])

    # this doesn't seem to be set for some reason
    df['Bookshelves'].fillna('read', inplace=True)

    # split the series name/number out from the title
    s = df['Title'].str.extract('(?P<Title>.+?)(?: \((?P<Series>.+?),? +#(?P<Entry>\d+)(?:; .+?)?\))?$')
    df = df.rename(columns={
        'Title': 'Original Title',
    }).join(s)

    # the year it's scheduled for (if any)
    df['Scheduled'] = df['Bookshelves'].str.extract(r'\b(\d{4})\b')

    return df


### filtering ##################################################################

# returns books on all of the shelves
def on_shelves(df, shelves=[], others=[]):
    if shelves:
        df = df[df['Exclusive Shelf'].isin(shelves)]
    for shelf in others:
        df = df[df['Bookshelves'].str.contains(r'\b{}\b'.format(shelf))]

    return df

