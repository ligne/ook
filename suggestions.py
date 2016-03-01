#!/usr/bin/python
# -*- coding: utf-8 -*-

import math
import sys
import argparse
import pandas as pd

def show_nearby(df, index, size):
    s = size - 3
    return df.iloc[(index-s):(index+size)]


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

df = pd.concat([pd.read_csv(f, sep='\t', names=['words', 'filename', 'title']) for f in files])  \
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
