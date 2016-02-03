#!/usr/bin/python
# -*- coding: utf-8 -*-

import math
import pandas as pd

def show_nearby(df, index, size=5):
    return df.iloc[(index-size):(index+size)]


f = 'wordcounts/books-lengths.txt'

df = pd.read_csv(f, sep='\t', names=['words', 'filename', 'title']).sort(['words'])
df = df.reset_index(drop=True)


median_ix = int(math.floor(len(df.index)/2))
mean_ix = df[df.words > int(df.mean()['words'])]['words'].index[0]

suggestions = pd.concat([
    show_nearby(df, median_ix),
    show_nearby(df, mean_ix)
], ignore_index=True).drop_duplicates()

suggestion_median = int(math.floor(len(suggestions.index)/2))

for row in show_nearby(suggestions, suggestion_median, 7).iterrows():
    print '{words:7d}  {title}'.format(**row[1])

