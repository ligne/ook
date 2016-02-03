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
parser.add_argument('csv_file')
parser.add_argument('size', type=int, nargs='?', default=10)
args = parser.parse_args()

f = args.csv_file
size = args.size

# read in the CSV, sort it, and set the index to match the new order.
df = pd.read_csv(f, sep='\t', names=['words', 'filename', 'title'])  \
       .sort(['words'])                                              \
       .reset_index(drop=True)

median_ix = int(math.floor(len(df.index)/2))
mean_ix = df[df.words > df.mean().words].index[0]

suggestions = pd.concat([
    show_nearby(df, median_ix, size),
    show_nearby(df, mean_ix, size)
], ignore_index=True).drop_duplicates()

suggestion_median = int(math.floor(len(suggestions.index)/2))

for row in show_nearby(suggestions, suggestion_median, size).iterrows():
    print '{words:7d}  {title}'.format(**row[1])

