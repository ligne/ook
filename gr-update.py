#!/usr/bin/python3
# -*- coding: utf-8 -*-

import time
import yaml
import datetime
import re
import sys
from xml.etree import ElementTree
from dateutil.parser import parse
import pandas as pd

import reading.goodreads
from reading.compare import compare


df = reading.goodreads.get_books()
df = df.set_index('Book Id')

#patches = pd.read_csv('data/goodreads_library_export.csv', index_col=0)
#patches.loc[:,'Number of Pages'].fillna('', inplace=True)

#df['Number of Pages'] = df['Number of Pages'].combine(patches['Number of Pages'], lambda x2, x1: x1 if x1 else x2)
#df.loc[:,'Number of Pages'].fillna('', inplace=True)
#
#df['Number of Pages'] = df['Number of Pages'].astype(str)

#df['Original Publication Year'] = patches['Original Publication Year']

old = pd.read_csv('gr-api.csv', index_col=0, dtype=object)

#df.sort_index().to_csv('gr-api.csv', float_format='%.f')

diff = compare(old, df)
if diff:
    print(diff)
    print('******************')

reading.compare._changed(old.fillna(''), df.fillna(''))

# vim: ts=4 : sw=4 : et
