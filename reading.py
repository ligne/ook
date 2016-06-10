#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import glob

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np


EBOOK_WORDCOUNTS = 'data/test.csv'
GR_HISTORY = 'data/goodreads_library_export.csv'

ix = pd.DatetimeIndex(start='2016-01-01', end='today', freq='D')

df = pd.read_csv(GR_HISTORY)

# patch up the data
start_dates = [
    (35220, '2016/01/01'),  # Red Badge of Courage
]
page_counts = [
    (20618571, 316),  # Tulipe noire
]

for (ii, val) in start_dates:
    df.loc[df['Book Id'] == ii,'Date Added'] = val

for (ii, val) in page_counts:
    if df.loc[df['Book Id'] == ii,'Number of Pages'].any():
        print "already got a page count for", ii
    df.loc[df['Book Id'] == ii,'Number of Pages'] = val


def added_pages(shelf):
    pending = df[df['Exclusive Shelf'] == shelf]
    if shelf == 'read':
        pending = pending.dropna(subset=['Date Read'])

    return pending.set_index(pd.to_datetime(pending['Date Added']))  \
                  .resample('D', how='sum')  \
                  .reindex(index=ix)  \
                  .fillna(0) \
                  .cumsum()['Number of Pages']


def completed_pages(shelf):
    pending = df[df['Exclusive Shelf'] == shelf]
    pending = pending[pending['Date Read'] > '2016']

    return pending.set_index(pd.to_datetime(pending['Date Read']))  \
                  .resample('D', how='sum')  \
                  .reindex(index=ix)  \
                  ['Number of Pages'] \
                  .fillna(0) \
                  .cumsum()


def added_ebook_pages():
    # get current value from actual files
    current_words = get_ebook_words()

    # read from local data cache
    df = pd.read_csv(EBOOK_WORDCOUNTS, index_col=0, parse_dates=True)

    last_words = df.ix[-1].values[0].__int__()

    # update if it's changed
    if last_words != current_words:
        df.ix[pd.to_datetime('today')] = current_words

    # save new data
    df.to_csv(EBOOK_WORDCOUNTS)

    # fill out the missing values
    s = df.reindex(index=ix).fillna(method='ffill')['words']

    # return, converted to pages
    return s / 390


# returns the current wordcount for all books
# FIXME eventually get this from the actual files (wordcounts.py)
def get_ebook_words():
    return get_all_ebook_words().ix[-1].__int__()

def get_all_ebook_words():
    import shelve
    import datetime
    stats = shelve.open('../ebooks/.stats.pickle')
    s = [ item for x in ['books', 'non-fiction', 'short-stories'] for item in stats[x+'|']  ]
    data = [int(x['total'])                               for x in s if 'total' in x]
    ts   = [datetime.datetime.utcfromtimestamp(x['time']) for x in s if 'total' in x]
    d = pd.Series(data=data, index=ts).resample('s', how='sum').resample('D', how='last')
    d.dropna().to_csv(EBOOK_WORDCOUNTS, header=['words'], index_label='date')
    return d


def reading_rate():
    completed = df.dropna(subset=['Date Read'])
    completed = completed.set_index(pd.to_datetime(completed['Date Read']))  \
                         .resample('D', how='sum')  \
                         .reindex(index=ix)  \
                         .fillna(0)

    return pd.expanding_mean(completed['Number of Pages']) * 365.2425


#################################################################################

rate = reading_rate()

p = pd.DataFrame({
    'elsewhere': added_pages('elsewhere'),
    'ebooks'   : added_ebook_pages(),
    'pending'  : added_pages('currently-reading') + added_pages('pending') + added_pages('read') - completed_pages('read'),
}, index=ix)

# scale by the reading rate at that time
p = p.divide(rate, axis=0)

# truncate to the interesting bit (after i'd added my books and those from home)
p = p.ix['2016-05-13':]

# sort so the largest is on top, and stack
p[p.max().order().index].cumsum(axis=1).plot()

# prettify and save
plt.grid(True)
#plt.legend(loc='center left', bbox_to_anchor=(1.0, 0.5))

plt.savefig('images/backlog.png')
plt.close()

