#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import glob

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

import wordcounts


EBOOK_WORDCOUNTS = 'data/ebook_wordcounts.csv'
GR_HISTORY = 'data/goodreads_library_export.csv'

ix = pd.DatetimeIndex(start='2016-01-01', end='today', freq='D')

### load the data and patch it up ##############################################

df = pd.read_csv(GR_HISTORY)

start_dates = [
    (35220, '2016/01/01'),  # Red Badge of Courage
]
page_counts = [
    (20618571, 316),  # Tulipe noire
    (601684,  1317),  # Quarante ans de suspense
]

for (ii, val) in start_dates:
    df.loc[df['Book Id'] == ii,'Date Added'] = val

for (ii, val) in page_counts:
    if df.loc[df['Book Id'] == ii,'Number of Pages'].any():
        print "already got a page count for", ii
    df.loc[df['Book Id'] == ii,'Number of Pages'] = val


################################################################################

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
    df = pd.read_csv(EBOOK_WORDCOUNTS, index_col=0, header=None, parse_dates=True, squeeze=True)

    # update if it's changed
    if df.ix[-1] != current_words:
        df.ix[pd.to_datetime('today')] = current_words

    # save new data
    df.to_csv(EBOOK_WORDCOUNTS)

    # fill out the missing values
    s = df.reindex(index=ix).fillna(method='ffill')

    # return, converted to pages
    return s / 390


# returns the current wordcount for all books
def get_ebook_words():
    import os
    total = 0
    for d in 'short-stories', 'books', 'non-fiction':
        d = os.environ['HOME'] + '/.kindle/documents/' + d
        files = os.walk(d).next()[2]
        for f in files:
            if f == 'My Clippings.txt':
                continue
            path = d + '/' + f
            fi = wordcounts.file_infos(path)
            total += fi['words']

    return total


# in pages per day...
def daily_reading_rate():
    completed = df.dropna(subset=['Date Read'])
    completed = completed.set_index(pd.to_datetime(completed['Date Read']))  \
                         .resample('D', how='sum')  \
                         .reindex(index=ix)  \
                         .fillna(0)

    return pd.expanding_mean(completed['Number of Pages'])


# ...or pages per year
def annual_reading_rate():
    return daily_reading_rate() * 365.2425


def save_image(df, name):
    # truncate to the interesting bit (after i'd added my books and those from home)
    df = df.ix['2016-05-13':]

    # stack and plot
    df.cumsum(axis=1).plot()

    # force the bottom of the graph to zero
    ylim = plt.ylim()
    plt.ylim([ min(ylim[0], 0), ylim[1] ])

    # prettify and save
    plt.grid(True)
    plt.legend(loc='center left', bbox_to_anchor=(1.0, 0.5))
    plt.savefig('images/{}.png'.format(name), bbox_inches='tight')
    plt.close()


#################################################################################

if __name__ == "__main__":
    p = pd.DataFrame({
        'elsewhere': added_pages('elsewhere'),
        'ebooks'   : added_ebook_pages(),
        'pending'  : added_pages('currently-reading') + added_pages('pending') + added_pages('read') - completed_pages('read'),
    }, index=ix, columns=['pending', 'ebooks', 'elsewhere'])

    # number of pages
    save_image(p, 'pages')

    # scale by the reading rate at that time
    p = p.divide(annual_reading_rate(), axis=0)
    save_image(p, 'backlog')

