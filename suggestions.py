#!/usr/bin/python
# -*- coding: utf-8 -*-

import math
import sys
import yaml
import argparse
import pandas as pd


GR_HISTORY = 'data/goodreads_library_export.csv'


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


if __name__ == "__main__":
    df = get_books()

    # read in the options.
    parser = argparse.ArgumentParser()
    parser.add_argument('args', nargs='+')
    args = parser.parse_args()

    files = args.args

    try:
        size = int(files[-1])
        files.pop()
    except:
        size = 10

    df = pd.concat([pd.read_csv(f, sep='\t', names=['words', 'title', 'author']) for f in files])  \
           .sort(['words'])         \
           .reset_index(drop=True)

    # read in the CSVs, sort them, and set the index to match the new order.

    median_ix = int(math.floor(len(df.index)/2))
    mean_ix = df[df.words > df.mean().words].index[0]

    suggestions = pd.concat([
        show_nearby(df, median_ix, size),
        show_nearby(df, mean_ix, size)
    ], ignore_index=True).drop_duplicates()

    suggestion_median = int(math.floor(len(suggestions.index)/2))

    for row in show_nearby(suggestions, suggestion_median, size).iterrows():
        print '{words:7d}  {title}'.format(**row[1])

# vim: ts=4 : sw=4 : et
