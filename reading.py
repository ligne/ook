#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import glob
import yaml
import datetime
import re

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

import wordcounts

# TODO
#   + gantt-style chart of started/ended/pages:  http://stackoverflow.com/questions/18066781/create-gantt-plot-with-python-matplotlib
#   + number of books over time


EBOOK_WORDCOUNTS = 'data/ebook_wordcounts.csv'
GR_HISTORY = 'data/goodreads_library_export.csv'

ix = pd.DatetimeIndex(start='2016-01-01', end='today', freq='D')
today = pd.to_datetime('today')
tomorrow = today + pd.Timedelta('1 day')


### load the data and patch it up ##############################################

def get_books():
    df = pd.read_csv(GR_HISTORY, index_col=0)

    with open('data/fixes.yml') as fh:
        df.update(pd.DataFrame(yaml.load(fh)).set_index(['Book Id']))

    for column in ['Date Read', 'Date Added']:
        df[column] = pd.to_datetime(df[column])

    # this doesn't seem to be set for some reason
    df['Bookshelves'].fillna('read', inplace=True)

    return df


df = get_books()

################################################################################

# from shelf, in direction = date added/read.
def changed_pages(df, shelf, direction):
    return df[df['Exclusive Shelf'] == shelf] \
                  .set_index([direction])  \
                   ['Number of Pages']  \
                  .resample('D', how='sum')  \
                  .reindex(index=ix)  \
                  .fillna(0)


# number of pages added by day
def added_pages(shelf):
    pending = df
    # ignore read books where no end date is set
    if shelf == 'read':
        pending = df.dropna(subset=['Date Read'])
    return changed_pages(pending, shelf, 'Date Added').cumsum()


# number of pages removed by day
def completed_pages(shelf):
    return changed_pages(df, shelf, 'Date Read').cumsum()


# total number of pages of ebooks by day
def ebook_pages():
    # get current value from actual files
    current_words = get_ebook_words()

    # read local data cache, and update if necessary
    df = pd.read_csv(EBOOK_WORDCOUNTS, index_col=0, header=None, parse_dates=True, squeeze=True)
    if df.ix[-1] != current_words:
        df.ix[pd.to_datetime('today')] = current_words
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
    return pd.expanding_mean(changed_pages(df, 'read', 'Date Read'))


# ...or pages per year
def annual_reading_rate():
    return daily_reading_rate() * 365.2425


def save_image(df, name):
    df.plot()

    # force the bottom of the graph to zero
    ylim = plt.ylim()
    plt.ylim([ min(ylim[0], 0), ylim[1] ])

    # prettify and save
    plt.grid(True)
    plt.legend(loc='center left', bbox_to_anchor=(1.0, 0.5))
    plt.savefig('images/{}.png'.format(name), bbox_inches='tight')
    plt.close()


# draw graphs of my backlog over time, both as a number of pages and scaled by
# reading rate.
def backlog():
    p = pd.DataFrame({
        'elsewhere': added_pages('elsewhere'),
        'ebooks'   : ebook_pages(),
        'pending'  : added_pages('currently-reading') + added_pages('pending') + added_pages('read') - completed_pages('read'),
    }, index=ix, columns=['pending', 'ebooks', 'elsewhere'])

    # truncate to the interesting bit (after i'd added my books and those from home)
    p = p.ix['2016-05-13':].cumsum(axis=1)

    rate = annual_reading_rate().reindex(p.index)

    # number of pages
    save_image(p, 'pages')

    # scale by the reading rate at that time
    p = p.divide(rate, axis=0)
    save_image(p, 'backlog')


# plot average scores as a histogram
def draw_rating_histogram(df):
    ax = df['Average Rating'].plot(kind='hist', bins=100, title='Average Ratings')
    ax.set_xlim(1,5)
    plt.savefig('images/average_scores.png')
    plt.close()


# number of new authors a year
def new_authors(df):
    authors = df.dropna(subset=['Date Read']).sort('Date Read')

    authors = authors.groupby('Author')

    # how many new authors a year
    first = authors.first()
    first['year'] = first['Date Read'].dt.year
    print first['year']
    first.groupby('year').size().plot()

    # force the bottom of the graph to zero
    ylim = plt.ylim()
    plt.ylim([ min(ylim[0], 0), ylim[1] ])

    # prettify and save
    name = 'new_authors'
    plt.savefig('images/{}.png'.format(name), bbox_inches='tight')
    plt.close()


# plot reading rate so far.
def reading_rate():
    pending = df.dropna(subset=['Date Read'])
    completed = changed_pages(pending, 'read', 'Date Read')

    current_pages = df[df['Exclusive Shelf'] == 'currently-reading']['Number of Pages'].sum()

    reading = completed.copy()
    reading.ix[tomorrow] = current_pages

    p = pd.DataFrame({
        'Completed': pd.expanding_mean(completed),
        'Reading':   pd.expanding_mean(reading).ix[-2:],
    }, index=reading.index)

    p.plot(title='Pages read per day')
    name = 'rate'

    # prettify and save
    plt.grid(True)
    #plt.savefig('images/{}.png'.format(name), bbox_inches='tight')
    plt.savefig('images/{}.png'.format(name))
    plt.close()


################################################################################

def is_current_year(year):
    return int(today.year) == int(year)


def _days_remaining(year):
    if is_current_year(year):
        return (datetime.datetime(int(year), 12, 31) - today).days
    else:
        return 365  # FIXME


# books i've pencilled in to read this year
def scheduled():
    pending = df[df['Exclusive Shelf'] != 'read']

    years = df['Bookshelves'].str.split(', ').values
    years = filter(lambda x:re.search(r'^\d{4}$', x), list(set([item for sublist in years for item in sublist])))

    for year in years:
        pattern = r'\b{}\b'.format(year)
        p = pending[pending['Bookshelves'].str.contains(pattern)]

        pages_remaining = p['Number of Pages'].sum()
        if is_current_year(year):
            pages_remaining += added_pages('currently-reading').ix[-1]

        rate = daily_reading_rate().ix[-1]

        days_remaining = _days_remaining(year)
        days_required = pages_remaining / rate

        if days_required > days_remaining:
            days_over = days_required - days_remaining
            pages_over = pages_remaining - (days_remaining * rate)
            needed_rate = pages_remaining/days_remaining

            print "Too many book for this year!"
            print "    {:.0f} pages to read in {:.0f} days.".format(pages_remaining, days_remaining)
            print "    {:.0f} days at current rate".format(days_required)
            print "    {:.0f} days/{:.0f} pages over".format(days_over, pages_over)
            print "    {:.1f}pp/day to read them all ({:.1f} currently)".format(needed_rate, rate)

        s = pd.Series([days_remaining, days_required], index=['Days remaining', 'Days required'])
        s = pd.Series([days_required], index=['Days required'])
        s = pd.Series({ 'Days required': days_required })

        s.plot(kind='bar', title='Scheduled books ({})'.format(year))
        plt.axhline(days_remaining)
        filename = 'images/scheduled-{}.png'.format(year)
        plt.savefig(filename, bbox_inches='tight')
        plt.close()


################################################################################

def _make_rating_scatterplot(data, name, **args):
    import seaborn as sns

    g = sns.JointGrid(x="My Rating", y="Average Rating", data=data)
    g = g.plot_joint(sns.regplot, **args)
    g = g.plot_marginals(sns.distplot, kde=False, bins=np.arange(1,6, 0.05))

    g.ax_marg_x.set_xticks(np.arange(1,6))
    g.ax_marg_y.set_yticks(np.arange(1,6))

    g.ax_marg_x.set_xlim(1,5.1)
    g.ax_marg_y.set_ylim(1,5)

    plt.savefig('images/' + name)
    plt.close()


def rating_scatter():
    # select only books i've read where all of these columns are set
    scoring = df[df['Exclusive Shelf'] == 'read']  \
                .dropna(subset=['My Rating'])       \
                .dropna(subset=['Average Rating'])

    scoring['year'] = pd.to_datetime(scoring['Date Read']).dt.year
    scoring = scoring[(scoring['year'].isnull()) | (scoring['year'] > 2014)]

    _make_rating_scatterplot(scoring, 'scatter_2.png', x_jitter=.1)
    _make_rating_scatterplot(scoring, 'scatter.png',   x_estimator=np.mean)


#################################################################################

if __name__ == "__main__":
    scheduled()
    backlog()
    #new_authors(df)
    #draw_rating_histogram(df)
    reading_rate()
    rating_scatter()

