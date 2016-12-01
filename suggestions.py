#!/usr/bin/python
# -*- coding: utf-8 -*-

import math
import sys
import yaml
import datetime
import argparse

import pandas as pd

import reading


today = datetime.date.today()


# return a list of the authors i've read recently (this year, or within the
# last 6 months).
#
# FIXME also books that are read but don't have a date?
def already_read(df):
    read = df[df['Exclusive Shelf'] == 'read'].copy()
    read['age'] = today - read['Date Read']
    old = read[(read['Date Read'].dt.year == today.year) | (read['age'] < '180 days')]
    return old['Author'].values


ignored_authors = already_read(reading.get_books())

# filter out authors from the list
def ignore_authors(df):
    return df[~df['author'].isin(ignored_authors)]


def _scheduled_for_year(df, year):
    df = df[df['Bookshelves'].fillna('').str.contains(str(year))]
    df = df[['Author', 'Number of Pages', 'Title']]
    df.columns = ['author', 'words', 'title']
    return df.sort(['words']).reset_index(drop=True)


# authors whose books are still scheduled for this year
def _scheduled_authors(df):
    return _scheduled_for_year(df, today.year)['author'].values


# books scheduled for the current year, ignoring those i read recently.
def scheduled(df):
    return ignore_authors(_scheduled_for_year(df, today.year))


# Scheduled for next year but not by already read author
def bump(df):
    df = df[~df['Author'].isin(_scheduled_authors(df))]
    df = _scheduled_for_year(df, today.year + 1)
    return ignore_authors(df)


# books by authors that i've read before
def old_authors(df):
    # list of all authors i've previously read
    authors = df[df['Exclusive Shelf'] == 'read']['Author'].values
    scheduled_authors = _scheduled_authors(df)
    df = df[df['Exclusive Shelf'].isin(['pending', 'elsewhere'])]
    df = df[['Author', 'Number of Pages', 'Title']]
    df.columns = ['author', 'words', 'title']
    df = df[df['author'].isin(authors)]

    # remove ones i've already read this year
    # removed scheduled authors
    df = df[~df['author'].isin(scheduled_authors)]

    return ignore_authors(df).sort(['words'])


# books by authors i've not read before
# FIXME only unscheduled?
def new_authors(df):
    # list of all authors i've previously read
    authors = df[df['Exclusive Shelf'] == 'read']['Author'].values

    df = df[df['Exclusive Shelf'].isin(['pending', 'elsewhere'])]

    df = df[['Author', 'Number of Pages', 'Title']]
    df.columns = ['author', 'words', 'title']

    return df[~df['author'].isin(authors)].sort(['words'])


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


# selects $size rows from $df, centred around $index
def show_nearby(df, index, size):
    s = size / 2
    return df.iloc[max(0, index - s):(index + s)]


# prints it out.  FIXME hande missing author better.  FIXME allow sorting/grouping by author?
def print_rows(df):
    for ix, row in df.iterrows():
        print '{words:7.0f}  {title} ({author})'.format(**row)


################################################################################

if __name__ == "__main__":
    df = reading.get_books()
    authors = already_read(df)

    # read in the options.
    parser = argparse.ArgumentParser()
    parser.add_argument('args', nargs='*')
    parser.add_argument('--scheduled', action="store_true")
    parser.add_argument('--bump', action="store_true")
    parser.add_argument('--new-authors', action="store_true")
    parser.add_argument('--old-authors', action="store_true")
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
    elif args.scheduled:
        df = scheduled(df)
    elif args.bump:
        df = bump(df)
    elif args.old_authors:
        df = old_authors(df)
    elif args.new_authors:
        df = new_authors(df)
    else:
        # use the goodreads list
        df = df[df['Exclusive Shelf'] == 'pending']

        # remove books if there's already an earlier one in the series
        # drop_duplicates() treats NaNs as being the same, so need to be more
        # circuitous.
        df = df.sort('Entry')
        df = df[(~df.duplicated(subset=['Author', 'Series']))|(df['Series'].isnull())]

        df = df[['Author', 'Number of Pages', 'Title']]
        df.columns = ['author', 'words', 'title']
        df = df.sort(['words']).reset_index(drop=True)

        df = ignore_authors(df)
        df = limit_rows(df, size)

    print_rows(df)

# vim: ts=4 : sw=4 : et
