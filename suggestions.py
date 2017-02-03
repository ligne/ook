#!/usr/bin/python
# -*- coding: utf-8 -*-

import math
import sys
import datetime
import argparse

import pandas as pd

import reading


today = datetime.date.today()

default_shelves = [
    'pending',
    'elsewhere',
    'ebooks',
    'kindle',
]


# return a list of the authors i'm currently reading, or have read recently
# (this year, or within the last 6 months).
#
# FIXME also books that are read but don't have a date?
def recent_authors(df):
    this_year = df['Date Read'].dt.year == today.year
    recent = (today - df['Date Read']) < '180 days'
    current = df['Exclusive Shelf'] == 'currently-reading'

    return df[this_year | recent | current].Author.values


# filter out authors from the list
def ignore_authors(df):
    return df[~df['Author'].isin(recent_authors(reading.get_books()))]


def _scheduled_for_year(df, year):
    return df[df.Scheduled == str(year)]


# authors whose books are still scheduled for this year
def _scheduled_authors(df):
    return _scheduled_for_year(df, today.year)['Author'].values


# books scheduled for the current year
def scheduled(df):
    return _scheduled_for_year(df, today.year)


# Scheduled for next year but not by already read author
def bump(df):
    df = df[~df['Author'].isin(_scheduled_authors(df))]
    return _scheduled_for_year(df, today.year + 1)


# books by authors that i've read before
def old_authors(df):
    authors = reading.get_books(shelves=['read']).Author.values
    return df[df['Author'].isin(authors)]


# books by authors i've not read before
def new_authors(df):
    authors = reading.get_books(shelves=['read']).Author.values
    return df[~df['Author'].isin(authors)]


# books by nationalities that i've read before
def old_nationalities(df):
    nationalities = reading.get_books(shelves=['read']).Nationality.values
    return df[df['Nationality'].isin(nationalities)]


# books by nationalities i've not read before
def new_nationalities(df):
    nationalities = reading.get_books(shelves=['read']).Nationality.values
    return df[~df['Nationality'].isin(nationalities)]


def merge_volumes(df):
    pages = df.groupby(['Author', 'Title'], as_index=False)['Number of Pages'].sum()
#     df.ix[pages.index,'Number of Pages'] = pages

    return df.groupby(['Author', 'Title'], as_index=False).aggregate({
        'Number of Pages': 'sum',
        'Series': 'first',
        'Entry': 'first',
    })

    return df


# pick (FIXME approximately) $size rows from around the median and mean of the
# list.
def limit_rows(df, size):
    df = df.sort('Number of Pages').reset_index(drop=True)

    if not len(df):
        return df

    median_ix = int(math.floor(len(df.index) / 2))
    mean_ix = df[df['Number of Pages'] >= df.mean()['Number of Pages']].index[0]

    suggestions = pd.concat([
        show_nearby(df, median_ix, size),
        show_nearby(df, mean_ix, size),
    ], ignore_index=True).drop_duplicates()

    suggestion_median = int(math.floor(len(suggestions.index) / 2))

    return show_nearby(suggestions, suggestion_median, size)


# selects $size rows from $df, centred around $index
def show_nearby(df, index, size):
    s = size / 2
    return df.iloc[max(0, index - s):(index + s)]


# prints it out.
def print_rows(df):
    for ix, row in df.sort('Number of Pages').iterrows():
        fmt = '{Number of Pages:4.0f}  {Title}'
        if row['Author']:
            fmt += ' ({Author})'
        print fmt.format(**row)


################################################################################

# modes:
#   scheduled
#       scheduled for this year.
#       next in series
#       not read in the last 6 months (same year is fine).
#           less than that is ok for authors i expect to read more of?  how many scheduled and read by that author this year, divide into equal chunks.
#   bump
#       scheduled for next year
#       not already scheduled for this year
#       not read recently
#   suggest
#       not scheduled
#       not read recently
#       next in series
#   schedule next
#       set year
#       not authors scheduled in that year
#       by authors i've got scheduled, or read recently, or where i've got a lot of their books
#
# filter:
#   number of suggestions.  don't limit if listing scheduled books
#
# output:
#   by word count
#   by author
#   by shelf
#

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    # miscellaneous
    parser.add_argument('--date', type=lambda d: datetime.datetime.strptime(d, '%Y-%m-%d'))
    parser.add_argument('--size', type=int, default=10)

    # mode
    parser.add_argument('--scheduled', action="store_true")
    parser.add_argument('--bump', action="store_true")

    # filter
    parser.add_argument('--shelves', nargs='+')
    parser.add_argument('--languages', nargs='+')
    parser.add_argument('--categories', nargs='+')
    parser.add_argument('--new-authors', action="store_true")
    parser.add_argument('--old-authors', action="store_true")
    parser.add_argument('--new-nationalities', action="store_true")
    parser.add_argument('--old-nationalities', action="store_true")
    # FIXME also gender, genre

    args = parser.parse_args()

    if args.date:
        today = args.date

    df = reading.get_books(
        shelves=args.shelves,
        languages=args.languages,
        categories=args.categories,
    )

    # only books i've yet to read
    df = reading.on_shelves(df, default_shelves)

    # filter
    if args.old_authors:
        df = old_authors(df)
    elif args.new_authors:
        df = new_authors(df)
    if args.old_nationalities:
        df = old_nationalities(df)
    elif args.new_nationalities:
        df = new_nationalities(df)

    # mode
    if args.scheduled:
        df = scheduled(df)
        df = merge_volumes(df)
    elif args.bump:
        df = bump(df)
    else:
        # remove books if there's already an earlier one in the series
        #
        # drop_duplicates() treats NaNs as being the same, so need to be more
        # circuitous.
        df = df.sort('Entry')
        df = df[(~df.duplicated(subset=['Author', 'Series']))|(df['Series'].isnull())]

        df = df[df.Scheduled.isnull()]
        df = limit_rows(df, args.size)

    # remove authors i've read recently
    df = ignore_authors(df)

    # output
    print_rows(df)


# vim: ts=4 : sw=4 : et
