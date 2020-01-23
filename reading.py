#!/usr/bin/python3
# -*- coding: utf-8 -*-

import datetime

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from reading.collection import Collection


# the cutoff year before which books are considered "old".
thresh = 1940

ix = pd.DatetimeIndex(start='2016-01-01', end='today', freq='D')
today = pd.Timestamp('today')
tomorrow = today + pd.Timedelta('1 day')


################################################################################

# from shelf, in direction = date added/read.
def _pages_changed(df, shelf, direction):
    return df[df.Shelf == shelf] \
        .set_index([direction])  \
        .Pages  \
        .resample('D')  \
        .sum()  \
        .reindex(index=ix)  \
        .fillna(0)


# number of pages added by day
def _pages_added(df, shelf):
    return _pages_changed(df, shelf, 'Added').cumsum()


# number of pages read by day
def _pages_read(df):
    return _pages_changed(df, 'read', 'Read').cumsum()


def save_image(df, name, start=None):
    df = df.loc[start:]

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
    df = Collection().df

    # FIXME _pages_added() can't see books added before 2016 without this
    df.loc[df.Added < '2016', 'Added'] = pd.Timestamp('2016-01-01')

    p = pd.DataFrame({
        'elsewhere': _pages_added(df, 'elsewhere'),
        'ebooks':    _pages_added(df, 'ebooks') + _pages_added(df, 'kindle'),
        'library':   _pages_added(df, 'library'),
        'pending':   _pages_added(df, 'currently-reading') + _pages_added(df, 'pending'),
        'read':      _pages_added(df, 'read') - _pages_read(df),
    }, index=ix, columns=['read', 'pending', 'ebooks', 'elsewhere', 'library'])

    p = p.cumsum(axis=1)

    # truncate to the interesting bit (after i'd added my books and those from
    # home)
    start = '2016-05-13'

    # number of pages
    save_image(p, 'pages', start=start)

    # scale by the reading rate at that time
    rate = _pages_changed(df, 'read', 'Read').expanding().mean() * 365.2425
    save_image(p.divide(rate, axis=0), 'backlog', start=start)


def increase():
    df = Collection().df

    p = pd.DataFrame({
        'elsewhere': _pages_added(df, 'elsewhere'),
        'ebooks':    _pages_added(df, 'ebooks') + _pages_added(df, 'kindle'),
        'library':   _pages_added(df, 'library'),
        'pending':   _pages_added(df, 'currently-reading') + _pages_added(df, 'pending'),
        'read':     -_pages_read(df),
    }, index=ix, columns=['read', 'pending', 'ebooks', 'elsewhere', 'library'])

    # work out how much to shift each column down by
    shift = p.where(p < 0, 0).sum(axis=1)
    # stack the columns, with any negatives set to zero
    heights = p.where(p > 0, 0).cumsum(axis=1)
    # shift everything down
    p = heights.add(shift, axis='index')

    save_image((p - p.shift(365)), 'increase', start='2018')


# number of new authors a year
def new_authors():
    authors = Collection(shelves=['read']).df
    first = authors.set_index('Read').sort_index().Author.drop_duplicates()
    first = first.resample('D').count().reindex(ix).fillna(0)
    first.rolling(window=365, min_periods=0).sum().plot()

    # force the bottom of the graph to zero
    ylim = plt.ylim()
    plt.ylim([min(ylim[0], 0), ylim[1]])

    plt.axhline(12, color='k', alpha=0.5)

    # prettify and save
    name = 'new_authors'
    plt.grid(True)
    plt.axvspan(today, first.index[-1], color='k', alpha=0.1)
    plt.title('New authors')
    plt.savefig('images/{}.png'.format(name), bbox_inches='tight')
    plt.close()


def median_date():
    read = Collection(shelves=['read']).df.dropna(subset=['Published'])

    read = read.set_index('Read').Published.resample('D').mean()

    read.rolling(window=365, min_periods=0).median()  \
        .rolling(window=30).mean()  \
        .reindex(ix).ffill().loc['2016':].plot()

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
def oldness():
    df = Collection(shelves=['read']).df.dropna(subset=['Published'])

    df = pd.DataFrame({
        'thresh': df.Published.apply(lambda x: (x < thresh and 1 or 0)),
        'total':  df.Published.apply(lambda x: 1),
        'Read': df.Read,
    }, index=df.index).set_index('Read')  \
                      .resample('D')      \
                      .sum()              \
                      .reindex(ix)        \
                      .fillna(0)

    df = df.rolling(window=365, min_periods=0).sum()
    (df.thresh / df.total).rolling(window=10, min_periods=0).mean().plot()

    # set to the full range
    plt.ylim([0, 1])

    plt.axhline(0.5, color='k', alpha=0.5)

    # prettify and save
    name = 'old_books'
    plt.grid(True)
    plt.title('Old books')
    plt.savefig('images/{}.png'.format(name), bbox_inches='tight')
    plt.close()


def gender():
    df = Collection(shelves=['read']).df
    df.Gender = df.Gender.fillna('unknown')

    df = df.pivot_table(
        values='Pages',
        index='Read',
        columns='Gender',
        aggfunc=np.sum,
        fill_value=0
    ).rolling('365d').sum()
    df.divide(df.sum(axis='columns'), axis='rows').loc['2017':].plot.area()

    # set to the full range
    plt.ylim([0, 1])

    # prettify and save
    name = 'gender'
    plt.grid(True)
    plt.title('Gender')
    plt.savefig('images/{}.png'.format(name), bbox_inches='tight')
    plt.close()


def language():
    df = Collection(shelves=['read']).df

    df.Language = df.Language.fillna('unknown')
    df = df.pivot_table(
        values='Pages',
        index='Read',
        columns='Language',
        aggfunc=np.sum,
        fill_value=0
    ).rolling('365d').sum()
    df.divide(df.sum(axis='columns'), axis='rows').loc['2017':].plot.area()

    plt.ylim([0, 1])

    # prettify and save
    name = 'language'
    plt.grid(True)
    plt.title('Languages')
    plt.savefig('images/{}.png'.format(name), bbox_inches='tight')
    plt.close()


def category():
    df = Collection(shelves=['read']).df

    df.Category = df.Category.fillna('unknown')
    df = df.pivot_table(
        values='Pages',
        index='Read',
        columns='Category',
        aggfunc=np.sum,
        fill_value=0
    ).rolling('365d').sum()
    df.divide(df.sum(axis='columns'), axis='rows').loc['2017':].plot.area()

    plt.ylim([0, 1])

    # prettify and save
    name = 'category'
    plt.grid(True)
    plt.title('Categories')
    plt.savefig('images/{}.png'.format(name), bbox_inches='tight')
    plt.close()


# plot total/new nationalities over the preceding year
def nationality():
    df = Collection(shelves=['read']).df

    # how many new nationalities a year
    authors = df.set_index('Read').sort_index()
    first = authors.Nationality.drop_duplicates()
    first = first.resample('D').count().reindex(ix, fill_value=0)

    # total number of distinct nationalities
    # FIXME use rolling apply?
    values = []
    for date in ix:
        start = (date - pd.Timedelta('365 days')).strftime('%F')
        end = date.strftime('%F')
        values.append(len(set(authors.loc[start:end].Nationality.values)))

    pd.DataFrame({
        'Distinct': pd.Series(data=values, index=ix),
        'New': first.rolling(window=365).sum(),
    }).plot()

    # force the bottom of the graph to zero and make sure the top doesn't clip.
    ylim = plt.ylim()
    plt.ylim([min(ylim[0], 0), ylim[1] + 1])

    # prettify and save
    name = 'nationalities'
    plt.grid(True)
    plt.axvspan(today, first.index[-1], color='k', alpha=0.1)
    plt.title('Nationalities')
    plt.savefig('images/{}.png'.format(name), bbox_inches='tight')
    plt.close()


# plot reading rate so far.
def reading_rate():
    df = Collection().df
    completed = _pages_changed(df, 'read', 'Read')

    current_pages = df[df.Shelf == 'currently-reading'].Pages.sum()

    reading = completed.copy()
    reading.loc[tomorrow] = current_pages

    p = pd.DataFrame({
        'Completed': completed.expanding().mean(),
        'Reading': reading.expanding().mean().iloc[-2:],
    }, index=reading.index)

    p.plot(title='Pages read per day')

    # prettify and save
    name = 'rate'
    plt.grid(True)
    plt.savefig('images/{}.png'.format(name))
    plt.close()


def rate_area():
    df = Collection(shelves=['read']).df

    df['ppd'] = df.Pages / ((df.Read - df.Started).dt.days + 1)

    g = pd.DataFrame(index=ix)

    for ii, row in df.sort_values(['Started']).iterrows():
        g[ii] = pd.Series({
            row.Started: row['ppd'],
            row.Read: 0,
        }, index=ix).ffill()

    g = g.plot(title='Reading rate', kind='area', lw=0)

    # prettify and save
    name = 'rate_area'
    plt.grid(True)
    # the legend doesn't help
    plt.legend().set_visible(False)
    plt.savefig('images/{}.png'.format(name), bbox_inches='tight')
    plt.close()


def doy():
    df = Collection(shelves=['read']).df

    df['Year'] = df.Read.dt.year
    df['Day of Year'] = df.Read.dt.dayofyear

    df.pivot_table(
        values='Pages',
        index='Day of Year',
        columns='Year',
        aggfunc=np.sum,
        fill_value=0
    ).reindex(range(1, 367), fill_value=0).cumsum().plot()

    plt.axvline(today.dayofyear, color='k', alpha=0.5)

#    plt.grid(True)
    for m in np.cumsum([0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])[:12]:
        plt.plot([m, 366], [0, 12000 * (1 - m / 366)], color='k', alpha=.2)

    # prettify and save
    name = 'doy'
    # the legend doesn't help
    plt.legend().set_visible(False)
    plt.title('Progress')
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


def scheduled_years(df):
    # FIXME
    years = set(df.Scheduled.dt.year.tolist())
    return sorted(list(years | {today.year}))


# plot reading schedule against time left, with warnings.
def scheduled():
    df = Collection().df

    rate = _pages_changed(df, 'read', 'Read').rolling(365).mean().iloc[-1]

    df.loc[df.Shelf == 'currently-reading', 'Scheduled'] = today
    df = df.dropna(subset=['Scheduled'])

    years = scheduled_years(df)

    fig, axes = plt.subplots(nrows=1, ncols=len(years), sharey=True)

    for year, ax in zip(years, axes):
        p = df[df.Scheduled.dt.year == year].Pages

        pages_remaining = p.sum()
        days_remaining = _days_remaining(year)
        days_required = pages_remaining / rate
        page_limit = days_remaining * rate

        margin = 1.1

        # give a margin before the warnings start.
        if days_required > margin * days_remaining:
            days_over = days_required - days_remaining
            pages_over = pages_remaining - page_limit
            needed_rate = pages_remaining / days_remaining

            print("Too many books for {}:".format(year))
            print("    {:.0f} pages to read in {:.0f} days.".format(pages_remaining, days_remaining))
            print("    {:.0f} days at current rate".format(days_required))
            print("    {:.0f} days/{:.0f} pages over".format(days_over, pages_over))
            print("    {:.1f}pp/day to read them all ({:.1f} currently)".format(needed_rate, rate))
            print()

        pages = p.sort_values().values
        pd.DataFrame([pages], index=[year]).plot.bar(stacked=True, ax=ax, rot=0, legend=False)

        ax.axhline(page_limit)
        if is_current_year(year):
            ax.axhspan(page_limit, page_limit * margin, color='k', alpha=0.1)

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

if __name__ == "__main__":
    doy()
    nationality()
    gender()
    language()
    category()
    rate_area()
    oldness()
    median_date()
    scheduled()
    backlog()
    increase()
    new_authors()
    reading_rate()

# vim: ts=4 : sw=4 : et
