#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

import pandas as pd

GR_HISTORY = 'data/goodreads_library_export.csv'

df = pd.read_csv(GR_HISTORY).sort('Date Added')
df = df.set_index(pd.to_datetime(df['Date Added']))


# missing page count
with pd.option_context('display.max_rows', 999, 'display.width', 1000):
    print '=== Missing page count ==='
    pending = df.ix['2016':][['Title', 'Author', 'Number of Pages']]
    print pending[pending.isnull().any(axis=1)][['Title', 'Author']]

