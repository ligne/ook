#!/usr/bin/python
# -*- coding: utf-8 -*-

import math
import sys
import yaml
import datetime
import argparse

import pandas as pd

# FIXME warn if any scheduled books are by authors i've already read this
# year

GR_HISTORY = 'data/goodreads_library_export.csv'
today = datetime.date.today()


def show_nearby(df, index, size):
    s = size - 3
    return df.iloc[(index-s):(index+size)]


# load the data and patch it up
def get_books():
    df = pd.read_csv(GR_HISTORY, index_col=0)

    with open('data/fixes.yml') as fh:
        df.update(pd.DataFrame(yaml.load(fh)).set_index(['Book Id']))

    for column in ['Date Read', 'Date Added']:
        df[column] = pd.to_datetime(df[column])

    return df


# return a list of the authors i've read recently (this year, or within the
# last 6 months).
#
# FIXME also books that are read but don't have a date?
def already_read(df):
    read = df[df['Exclusive Shelf'] == 'read'].copy()
    read['age'] = today - read['Date Read']
    old = read[(read['Date Read'].dt.year == today.year) | (read['age'] < '180 days')]
    return old['Author'].values


ignored_authors = already_read(get_books())


# filter out authors from the list
def ignore_authors(df):
    return df[~df['author'].isin(ignored_authors)]


# pick (FIXME approximately) $size rows from around the median and mean of the
# list.
def limit_rows(df, size):
    median_ix = int(math.floor(len(df.index)/2))
    mean_ix = df[df.words > df.mean().words].index[0]

    suggestions = pd.concat([
        show_nearby(df, median_ix, size),
        show_nearby(df, mean_ix, size)
    ], ignore_index=True).drop_duplicates()

    suggestion_median = int(math.floor(len(suggestions.index)/2))

    return show_nearby(suggestions, suggestion_median, size)


# prints it out.  FIXME hande missing author better.  FIXME allow sorting/grouping by author?
def print_rows(df):
    for row in df.iterrows():
        print '{words:7.0f}  {title} ({author})'.format(**row[1])


if __name__ == "__main__":
    df = get_books()
    authors = already_read(df)

    # read in the options.
    parser = argparse.ArgumentParser()
    parser.add_argument('args', nargs='*')
    args = parser.parse_args()

    files = args.args

    try:
        # only pop if it was numeric
        size = int(files[-1])
        files.pop()
    except:
        size = 10

    if len(files):
        # read in the CSVs, sort them, and set the index to match the new order.
        df = pd.concat([pd.read_csv(f, sep='\t', names=['words', 'title', 'author']) for f in files])  \
               .sort(['words'])         \
               .reset_index(drop=True)
        df = ignore_authors(df)
        df = limit_rows(df, size)
    else:
        # use the goodreads list
        df = df[df['Exclusive Shelf'] == 'pending']
        df = df[['Author', 'Number of Pages', 'Title']]
        df.columns = ['author', 'words', 'title']
        df = df.sort(['words']).reset_index(drop=True)
        # FIXME remove books if there's already an earlier one in the series

        df = ignore_authors(df)
        df = limit_rows(df, size)

    print_rows(df)

# vim: ts=4 : sw=4 : et
