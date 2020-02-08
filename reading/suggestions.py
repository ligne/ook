# vim: ts=4 : sw=4 : et

from textwrap import fill

from .scheduling import scheduled_books, scheduled_at
from .collection import Collection


# return a list of the authors i'm currently reading, or have read recently
# (this year, or within the last 6 months).
def _recent_author_ids(date):
    df = Collection().df  # want to consider *all* books

    return list(df[
        (df.Read.dt.year == date.year)
        | ((date - df.Read) < '180 days')
        | (df.Shelf == 'currently-reading')
    ].AuthorId)


def _read_author_ids():
    return list(Collection(shelves=['read']).df.AuthorId)


def _read_nationalities():
    return list(Collection(shelves=['read']).df.Nationality)


################################################################################

def scheduled(args):
    c = Collection(
        shelves=args.shelves,
        languages=args.languages,
        categories=args.categories,
        borrowed=args.borrowed,
        merge=True,
    )
    df = c.df

    df = df.loc[scheduled_at(c.all, args.date).index.intersection(df.index)]
    df = df[df.Scheduled.dt.year == args.date.year]
    args.all = True  # no display limit on scheduled books

    df = _filter(df, args)
    df = _sort(df, args)
    df = _reduce(df, args)
    _display(df, args)


# suggestions
def main(args):
    c = Collection(
        shelves=args.shelves,
        languages=args.languages,
        categories=args.categories,
        borrowed=args.borrowed,
        merge=True,
    )
    df = c.df

    # filter out recently-read, scheduled, etc
    df = df[~df.AuthorId.isin(_recent_author_ids(args.date))]
    df = df[~(df.Scheduled.notnull() | scheduled_books(df))]
    # FIXME eventually filter out "blocked" books

    df = _filter(df, args)
    df = _sort(df, args)
    df = _reduce(df, args)
    _display(df, args)


# do more filtering
def _filter(df, args):
    if args.old_authors:
        df = df[df.AuthorId.isin(_read_author_ids())]
    elif args.new_authors:
        df = df[~df.AuthorId.isin(_read_author_ids())]

    if args.old_nationalities:
        df = df[df.Nationality.isin(_read_nationalities())]
    elif args.new_nationalities:
        df = df[~df.Nationality.isin(_read_nationalities())]

    return df


# sort the suggestions
def _sort(df, args):
    if args.alpha:
        # FIXME use a more sortable version of the title
        df = df.sort_values(['Title', 'Author'])
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

