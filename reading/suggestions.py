# vim: ts=4 : sw=4 : et

from textwrap import fill

from .collection import Collection, read_authorids, read_nationalities
from .scheduling import scheduled_at, scheduled_books


# return a list of the authors i'm currently reading, or have read recently
# (this year, or within the last 6 months).
def _recent_author_ids(c, date):
    df = c.all

    return list(df[
        (df.Read.dt.year == date.year)
        | ((date - df.Read) < '180 days')
        | (df.Shelf == 'currently-reading')
    ].AuthorId)


################################################################################

def scheduled(args):
    c = (
        Collection.from_dir(merge=True)
        .shelves(args.shelves)
        .languages(args.languages)
        .categories(args.categories)
        .borrowed(args.borrowed)
    )
    df = c.df

    df = df.loc[scheduled_at(c.all, args.date).index.intersection(df.index)]
    df = df[df.Scheduled.dt.year == args.date.year]
    args.all = True  # no display limit on scheduled books

    df = _filter(df, args, c)
    df = _sort(df, args)
    df = _reduce(df, args)
    _display(df, args)


# suggestions
def main(args):
    c = (
        Collection.from_dir(merge=True)
        .shelves(args.shelves)
        .languages(args.languages)
        .categories(args.categories)
        .borrowed(args.borrowed)
    )
    df = c.df

    # filter out recently-read, scheduled, etc
    df = df[~df.AuthorId.isin(_recent_author_ids(c, args.date))]
    df = df[~(df.Scheduled.notnull() | scheduled_books(c.all).reindex(df.index))]
    # FIXME eventually filter out "blocked" books

    # remove other books by scheduled authors
    df = df[~df.AuthorId.isin(list(c.all[c.all.Scheduled.dt.year == args.date.year].AuthorId))]

    df = _filter(df, args, c)
    df = _sort(df, args)
    df = _reduce(df, args)
    _display(df, args)


# do more filtering
def _filter(df, args, c):
    if args.old_authors:
        df = df[df.AuthorId.isin(read_authorids(c))]
    elif args.new_authors:
        df = df[~df.AuthorId.isin(read_authorids(c))]

    if args.old_nationalities:
        df = df[df.Nationality.isin(read_nationalities(c))]
    elif args.new_nationalities:
        df = df[~df.Nationality.isin(read_nationalities(c))]

    return df


# sort the suggestions
def _sort(df, args):
    if args.alpha:
        # FIXME use a more sortable version of the title
        df = df.sort_values(['Title', 'Author'])
    elif args.age:
        df = df.sort_values(['Added', 'Title', 'Author'])
    else:
        df = df.sort_values(['Pages', 'Title', 'Author'])

    return df


# reduce the number of rows
def _reduce(df, args):
    if not args.all:
        index = len(df.index) // 2
        s = args.size / 2
        df = df.iloc[int(max(0, index - s)):int(index + s)]

    return df


# print out the suggestions
def _display(df, args):
    if args.words:
        fmt = '{Words:4.0f}  {Title} ({Author})'
    else:
        fmt = '{Pages:4.0f}  {Title} ({Author})'

    for (_, book) in df.iterrows():
        out = fmt.format(**book)
        if args.width:
            out = fill(out, width=args.width, subsequent_indent='      ')
        print(out)

