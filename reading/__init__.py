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

    # split the volume number and series name/number out from the title
    s = df['Title'].str.extract('(?P<Title>.+?)(?: (?P<Volume>I+))?(?: \((?P<Series>.+?),? +#(?P<Entry>\d+)(?:; .+?)?\))?$')
    df = df.rename(columns={
        'Title': 'Original Title',
    }).join(s)

    # lint doesn't want the fixes applying.
    if not no_fixes:
        with open('data/fixes.yml') as fh:
            df.update(pd.DataFrame(yaml.load(fh)).set_index(['Book Id']))

    with open('data/started.yml') as fh:
        df['Date Started'] = pd.DataFrame(yaml.load(fh)).set_index(['Book Id'])

    for column in ['Date Read', 'Date Added', 'Date Started']:
        df[column] = pd.to_datetime(df[column])

    # load information about the author
    a = load_yaml('authors')
    for col in ['Nationality', 'Gender']:
        df[col] = df['Author'].apply(lambda x: a.get(x, {}).get(col))

    # this doesn't seem to be set for some reason
    df['Bookshelves'].fillna('read', inplace=True)

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


# books added since $date
def added_since(df, date):
    return df[df['Date Added'] >= str(date)]


# books finished since $date
def read_since(df, date):
    return df[df['Date Read'] >= str(date)]


### Utilities ##################################################################

# returns a yaml data file's contents in a usable format.
def load_yaml(name):
    try:
        with open('data/{}.yml'.format(name)) as fh:
            a = yaml.load(fh)
    except:
        a = None
    return a or {}


# saves as yaml in a vaguely readable form.
def dump_yaml(name, data):
    with open('data/{}.yml'.format(name), 'w') as fh:
        yaml.dump(data, stream=fh, default_flow_style=False, encoding='utf-8', allow_unicode=True)

# vim: ts=4 : sw=4 : et
