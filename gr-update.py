#!/usr/bin/python3
# -*- coding: utf-8 -*-

import pandas as pd
import argparse

import reading.goodreads
from reading.compare import compare

parser = argparse.ArgumentParser()
parser.add_argument('-n', '--ignore-changes', action='store_true')
args = parser.parse_args()

df = reading.goodreads.get_books()
df = df.set_index('Book Id')

old = pd.read_csv('gr-api.csv', index_col=0, dtype=object)

if not args.ignore_changes:
    df.sort_index().to_csv('gr-api.csv', float_format='%.f')

reading.compare._changed(old.fillna(''), df.fillna(''))

diff = compare(old, df)
if diff:
    print('******************')
    print(diff)

# vim: ts=4 : sw=4 : et
