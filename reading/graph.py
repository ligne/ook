# vim: ts=4 : sw=4 : et

import datetime
import textwrap

# pylint: disable=wrong-import-position

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from .collection import Collection
from .config import config
from .scheduling import _set_schedules

# pylint: enable=wrong-import-position

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
    df = Collection.from_dir().df

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

    # truncate to the interesting bit
    start = '2016-04-17'

    # number of pages
    save_image(p, 'pages', start=start)

    # scale by the reading rate at that time
    rate = _pages_changed(df, 'read', 'Read').expanding().mean() * 365.2425
    save_image(p.divide(rate, axis=0), 'backlog', start=start)


def increase():
    df = Collection.from_dir().df

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
    authors = Collection.from_dir().shelves(["read"]).df
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
    read = Collection.from_dir().shelves(["read"]).df.dropna(subset=["Published"])

    read = read.set_index('Read').Published.resample('D').mean()

    read.rolling(window=365, min_periods=0).median()  \
        .rolling(window=30).mean()  \
        .reindex(ix).ffill().loc['2016':].plot()

    # set the top of the graph to the current year
    plt.ylim([plt.ylim()[0], today.year])

    # prettify and save
    name = 'median_date'
    plt.grid(True)
    plt.title('Median publication year')
    plt.savefig('images/{}.png'.format(name), bbox_inches='tight')
    plt.close()


def length():
    read = Collection.from_dir().shelves(["read"]).df
    read = read.set_index("Read").Pages.resample("D").mean()
    read.rolling(window=365, min_periods=0).mean().reindex(ix).ffill().loc["2016":].plot()

    # prettify and save
    name = "length"
    plt.grid(True)
    plt.title("Average length")
    plt.savefig("images/{}.png".format(name), bbox_inches="tight")
    plt.close()


# ratio of old/new books
def oldness():
    df = Collection.from_dir().shelves(["read"]).df.dropna(subset=["Published"])

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
    df = Collection.from_dir().shelves(["read"]).df
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
    df = Collection.from_dir().shelves(["read"]).df

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
    df = Collection.from_dir().shelves(["read"]).df

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
    df = Collection.from_dir().shelves(["read"]).df

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
    df = Collection.from_dir().df
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
    df = Collection.from_dir().shelves(["read"]).df

    df['ppd'] = df.Pages / ((df.Read - df.Started).dt.days + 1)

    g = pd.DataFrame(index=ix)

    for ii, row in df.sort_values(['Started']).iterrows():
        g[ii] = pd.Series({
            row.Started: row['ppd'],
            row.Read: 0,
        }, index=ix).ffill()

    g.plot(title='Reading rate', kind='area', lw=0)

    # prettify and save
    name = 'rate_area'
    plt.grid(True)
    # the legend doesn't help
    plt.legend().set_visible(False)
    plt.savefig('images/{}.png'.format(name), bbox_inches='tight')
    plt.close()


def doy():
    df = Collection.from_dir().shelves(["read"]).df.dropna(subset=["Read"])

    df["Year"] = df.Read.dt.year
    df["Day of Year"] = df.Read.dt.dayofyear

    df = df.pivot_table(
        values="Pages",
        index="Day of Year",
        columns="Year",
        aggfunc=np.sum,
        fill_value=0
    ).reindex(range(366), fill_value=0).cumsum()

    target = pd.Series({0: 0, 365: 12000}, index=range(366)).interpolate()
    df.sub(target, axis="index").plot()

    plt.axvline(today.dayofyear, color="k", alpha=0.5)

    # prettify and save
    name = "doy"
    plt.grid(True)
    plt.title("Progress")
    plt.savefig(f"images/{name}.png", bbox_inches="tight")
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
    return sorted(years | {today.year})


# plot reading schedule against time left, with warnings.
def scheduled():
    df = Collection.from_dir().df
    _set_schedules(df, config("scheduled"))

    rate = _pages_changed(df, 'read', 'Read').rolling(365).mean().iloc[-1]

    df.loc[df.Shelf == 'currently-reading', 'Scheduled'] = today
    df = df.dropna(subset=['Scheduled'])

    years = scheduled_years(df)[:3]

    _fig, axes = plt.subplots(nrows=1, ncols=len(years), sharey=True)

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

            print(textwrap.dedent(f"""\
                Too many books for {year}:
                    {pages_remaining:.0f} pages to read in {days_remaining:.0f} days
                    {days_required:.0f} days at current rate
                    {days_over:.0f} days/{pages_over:.0f} pages over
                    {needed_rate:.1f}pp/day to read them all ({rate:.1f} currently)
            """))

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

def main(_args):
    length()
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

