#!/usr/bin/python3

import datetime
import argparse

from reading.scheduling import scheduled_books
from reading.collection import Collection


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

# modes:
#   scheduled
#       scheduled for this year.
#       not read in the last 6 months (same year is fine).
#   suggest
#       not scheduled
#       not read recently
#       next in series
def parse_args():
    parser = argparse.ArgumentParser()

    # miscellaneous
    parser.add_argument(
        '--date',
        type=lambda d: datetime.datetime.strptime(d, '%Y-%m-%d'),
        default=datetime.date.today(),
    )
    # mode
    parser.add_argument('--scheduled', action="store_true")
    # filter
    parser.add_argument('--shelves', nargs='+', default=[
        'pending',
        'elsewhere',
        'ebooks',
        'kindle',
    ])
    parser.add_argument('--languages', nargs='+')
    parser.add_argument('--categories', nargs='+')
    parser.add_argument('--new-authors', action="store_true")
    parser.add_argument('--old-authors', action="store_true")
    parser.add_argument('--new-nationalities', action="store_true")
    parser.add_argument('--old-nationalities', action="store_true")
    parser.add_argument('--borrowed', action='store_true', default=None)
    # FIXME also gender, genre
    # sort
    parser.add_argument('--alpha', action='store_true')
    # display
    parser.add_argument('--size', type=int, default=10)
    parser.add_argument('--all', action="store_true")
    parser.add_argument('--width', type=int, default=None)
    parser.add_argument('--words', action="store_true")

    return parser.parse_args()


################################################################################

if __name__ == "__main__":
    args = parse_args()

    df = Collection(
        shelves=args.shelves,
        languages=args.languages,
        categories=args.categories,
        borrowed=args.borrowed,
        merge=True,
    ).df

    # mode
    if args.scheduled:
        # FIXME not quite the right thing...
        #df = reading.scheduling.scheduled_at(df, args.date)
        df = df[df.Scheduled.dt.year == args.date.year]
        args.all = True  # no display limit on scheduled books
    else:
        # otherwise suggestion mode
        # filter out recently-read, scheduled, etc
        df = df[~df.AuthorId.isin(_recent_author_ids(args.date))]
        df = df[~(df.Scheduled.notnull() | scheduled_books(df))]
        # FIXME eventually filter out "blocked" books

    # filter
    if args.old_authors:
        df = df[df.AuthorId.isin(_read_author_ids())]
    elif args.new_authors:
        df = df[~df.AuthorId.isin(_read_author_ids())]

    if args.old_nationalities:
        df = df[df.Nationality.isin(_read_nationalities())]
    elif args.new_nationalities:
        df = df[~df.Nationality.isin(_read_nationalities())]

    # sort
    if args.alpha:
        # FIXME use a more sortable version of the title
        df = df.sort_values(['Title', 'Author'])
    else:
        df = df.sort_values(['Pages', 'Title', 'Author'])

    # reduce
    if not args.all:
        index = len(df.index) // 2
        s = args.size / 2
        df = df.iloc[int(max(0, index - s)):int(index + s)]

    # display
    if args.words:
        fmt = '{Words:4.0f}  {Title} ({Author})'
    else:
        fmt = '{Pages:4.0f}  {Title} ({Author})'

    for (_, book) in df.iterrows():
        print(fmt.format(**book)[:args.width])

# vim: ts=4 : sw=4 : et
