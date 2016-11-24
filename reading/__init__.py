# -*- coding: utf-8 -*-

import sys
import yaml

import pandas as pd


GR_HISTORY = 'data/goodreads_library_export.csv'


################################################################################

# load the data and patch it up
def get_books(no_fixes=False):
    df = pd.read_csv(GR_HISTORY, index_col=0)

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

    return df

