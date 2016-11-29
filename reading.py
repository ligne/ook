#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import glob
import datetime
import re

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

import wordcounts
import reading


EBOOK_WORDCOUNTS = 'data/ebook_wordcounts.csv'

# the cutoff year before which books are considered "old".
thresh = 1940

ix = pd.DatetimeIndex(start='2016-01-01', end='today', freq='D')
today = pd.to_datetime('today')
tomorrow = today + pd.Timedelta('1 day')


df = reading.get_books()


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


# daily reading rate right now.
def current_reading_rate():
    return changed_pages(df, 'read', 'Date Read').mean()


def save_image(df, name):
    df.plot()

    # force the bottom of the graph to zero
    ylim = plt.ylim()
    plt.ylim([min(ylim[0], 0), ylim[1]])

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
        'pending'  : added_pages('currently-reading') + added_pages('pending'),
        'read'     : added_pages('read') - completed_pages('read'),
    }, index=ix, columns=['read', 'pending', 'ebooks', 'elsewhere'])

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
    ax.set_xlim(1, 5)
    plt.savefig('images/average_scores.png')
    plt.close()


# number of new authors a year
def new_authors(df):
    authors = df.dropna(subset=['Date Read']).sort('Date Read')

    next_year = today + pd.Timedelta('365 days')

    # how many new authors a year
    first = authors.drop_duplicates(['Author'])  \
                 .set_index('Date Read')  \
                 ['Author']  \
                 .resample('D', how='count')  \
                 .reindex(pd.DatetimeIndex(start='2015-01-01', end=next_year, freq='D'))  \
                 .fillna(0)

    pd.rolling_sum(first, window=365).ffill().ix['2016':].plot()

    # force the bottom of the graph to zero and make sure the top doesn't clip.
    ylim = plt.ylim()
    plt.ylim([min(ylim[0], 0), ylim[1] + 1])

    plt.axhline(12, color='k', alpha=0.5)

    # prettify and save
    name = 'new_authors'
    plt.grid(True)
    plt.axvspan(today, first.index[-1], color='k', alpha=0.1)
    plt.title('New authors')
    plt.savefig('images/{}.png'.format(name), bbox_inches='tight')
    plt.close()


def median_date(df):
    read = df[df['Exclusive Shelf'] == 'read'].dropna(subset=['Date Read'])

    read.loc[:,'Original Publication Year'].fillna(read['Year Published'], inplace=True)

    read = read.set_index('Date Read')  \
                ['Original Publication Year']  \
                .resample('D')

    read = pd.rolling_median(read, 365, min_periods=0)
    read = pd.rolling_mean(read, 30)

    read.reindex(ix).ffill().ix['2016':].plot()

    # set the top of the graph to the current year
    plt.ylim([plt.ylim()[0], today.year])

    plt.axhline(thresh, color='k', alpha=0.5)

    # prettify and save
    name = 'median_date'
    plt.grid(True)
    plt.title('Median publication year')
    plt.savefig('images/{}.png'.format(name), bbox_inches='tight')
    plt.close()


# ratio of old/new books
def oldness(df):
    read = df[df['Exclusive Shelf'] == 'read'].dropna(subset=['Date Read'])

    # use the edition year if the original publication year was missing
    read.loc[:,'Original Publication Year'].fillna(read['Year Published'], inplace=True)

    df['thresh'] = df['Original Publication Year'].apply(lambda x: (x < thresh and 1 or 0))
    df['total'] = df['Original Publication Year'].apply(lambda x: 1)

    df = df.set_index('Date Read')  \
           .resample('D', how='sum')  \
           .fillna(0)

    df['rate'] = (pd.rolling_sum(df.thresh, 365) / pd.rolling_sum(df.total, 365))

    pd.rolling_mean(df['rate'], 10, min_periods=0).reindex(ix).ffill().plot()

    # set to the full range
    plt.ylim([0, 1])

    plt.axhline(0.5, color='k', alpha=0.5)

    # prettify and save
    name = 'old_books'
    plt.grid(True)
    plt.title('Old books')
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

    # prettify and save
    name = 'rate'
    plt.grid(True)
    #plt.savefig('images/{}.png'.format(name), bbox_inches='tight')
    plt.savefig('images/{}.png'.format(name))
    plt.close()


def rate_area(df):
    df = df[df['Date Read'].dt.year >= 2016].copy()

    df['ppd'] = df['Number of Pages'] / ((df['Date Read'] - df['Date Started']).dt.days + 1)

    g = pd.DataFrame(index=ix)

    for ii, row in df.sort(['Date Started']).iterrows():
        g[ii] = pd.Series({
            row['Date Started']: row['ppd'],
            row['Date Read']: 0,
        }, index=ix).ffill()

    g = g.plot(title='Reading rate', kind='area')

    # prettify and save
    name = 'rate_area'
    plt.grid(True)
    # the legend doesn't help
    plt.legend().set_visible(False)
    plt.savefig('images/{}.png'.format(name), bbox_inches='tight')
    plt.close()


################################################################################

def is_current_year(year):
    return int(today.year) == int(year)


def _days_remaining(year):
    if is_current_year(year):
        return (datetime.datetime(int(year), 12, 31) - today).days
    else:
        return 365  # FIXME


def _scheduled_for_year(df, year):
    pattern = r'\b{}\b'.format(str(year))
    return df[df['Bookshelves'].str.contains(pattern)]


# books i've pencilled in to read this year
def scheduled():
    rate = current_reading_rate()

    years = df['Bookshelves'].str.split(', ').values
    years = filter(lambda x: re.search(r'^\d{4}$', x), list(set([item for sublist in years for item in sublist])))

    fig, axes = plt.subplots(nrows=1, ncols=len(years), sharey=True)
    sp = 0

    for year in sorted(years):
        p = _scheduled_for_year(df, year)

        pages_remaining = p['Number of Pages'].sum()
        if is_current_year(year):
            pages_remaining += added_pages('currently-reading').ix[-1]

        days_remaining = _days_remaining(year)
        days_required = pages_remaining / rate

        # give a 10% margin before the warnings start.
        if days_required > 1.1 * days_remaining:
            days_over = days_required - days_remaining
            pages_over = pages_remaining - (days_remaining * rate)
            needed_rate = pages_remaining / days_remaining

            print "Too many books for {}:".format(year)
            print "    {:.0f} pages to read in {:.0f} days.".format(pages_remaining, days_remaining)
            print "    {:.0f} days at current rate".format(days_required)
            print "    {:.0f} days/{:.0f} pages over".format(days_over, pages_over)
            print "    {:.1f}pp/day to read them all ({:.1f} currently)".format(needed_rate, rate)
            print

        ax = axes[sp]
        pd.Series({ year: pages_remaining }).plot(kind='bar', ax=ax, rot=0)
        ax.axhline(_days_remaining(year) * rate)

        sp += 1

    # set the right-hand ticks.  no labels except on final column.  do this
    # after all the graphs are drawn, so the y-axis scaling is correct.
    for ax in axes:
        axr = ax.twinx()
        axr.set_ylim([x / rate for x in ax.get_ylim()])
        if ax != axes[-1]:
            axr.set_yticklabels([])

    filename = 'images/scheduled.png'
    plt.savefig(filename, bbox_inches='tight')
    plt.close()


################################################################################

def _make_rating_scatterplot(data, name, **args):
    import seaborn as sns

    g = sns.JointGrid(x="My Rating", y="Average Rating", data=data)
    g = g.plot_joint(sns.regplot, **args)
    g = g.plot_marginals(sns.distplot, kde=False, bins=np.arange(1, 6, 0.05))

    g.ax_marg_x.set_xticks(np.arange(1, 6))
    g.ax_marg_y.set_yticks(np.arange(1, 6))

    g.ax_marg_x.set_xlim(0.9, 5.1)
    g.ax_marg_y.set_ylim(0.9, 5)

    plt.savefig('images/' + name)
    plt.close()


def rating_scatter():
    # select only books i've read where all of these columns are set
    scoring = df[df['Exclusive Shelf'] == 'read']  \
                .dropna(subset=['My Rating'])       \
                .dropna(subset=['Average Rating'])

    scoring['year'] = scoring['Date Read'].dt.year
    scoring = scoring[(scoring['year'].isnull()) | (scoring['year'] > 2014)]

    _make_rating_scatterplot(scoring, 'scatter_2.png', x_jitter=.1)
    _make_rating_scatterplot(scoring, 'scatter.png',   x_estimator=np.mean)


#################################################################################

if __name__ == "__main__":
    rate_area(df)
    oldness(df)
    median_date(df)
    scheduled()
    backlog()
    new_authors(df)
    #draw_rating_histogram(df)
    reading_rate()
    rating_scatter()

