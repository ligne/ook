#!/usr/bin/python

import sys
import re
import argparse

import reading
import reading.ebooks
from reading.author import Author
from reading.book import Book


# FIXME if there are arguments:
#   --book/--author, take arg(s), load books, filter, make sure there's only
#       one and use that.
#   --grid/--qid, set those as the values, including in the index. force a full fetch.
#
# read in the options.
if len(sys.argv) > 1:
    parser = argparse.ArgumentParser()
    parser.add_argument('--book', nargs='+')
    parser.add_argument('--author', nargs='+')
    parser.add_argument('--qid')
    parser.add_argument('--grid', type=int)
    args = parser.parse_args()

    print args.__dict__

    df = reading.get_books(fix_names=False)
    df = df.append(reading.ebooks.get_books(fix_names=False))

    if args.book:
        terms = args.book
        col = 'Title'
    elif args.author:
        terms = args.author
        col = 'Author'
    else:
        print "Either --book or --author must be specified"
        sys.exit()

    for term in terms:
        df = df[df[col].str.contains(term)]

    name = df[col].unique()

    if len(name) > 1:
        print "Not specific enough:"
        for term in name:
            print ' ', term
        sys.exit()
    if not len(df):
        print "Nothing found"
        sys.exit()

    # get the term
    name = name[0]
    print name

    # instantiate an object, set it, and fetch
    if args.book:
        o = Book(df.iloc[0], qid=args.qid, grid=args.grid)
    elif args.author:
        o = Author(name, qid=args.qid, grid=args.grid)

    o.fetch_missing()
    print o._item

#     Book.save()
#     Author.save()

    sys.exit()




df = reading.ebooks.get_books(fix_names=False)

for ix, book in df.iterrows():
    try:
        b = Book(book['Title'], book['Author'], book['Language'])
        b.fetch_missing()
        if len(b.get('AQIDs', [])) == 1:
            Author(book['Author'], qid=b.get('AQIDs')[0])
    except Exception as e:
        print e

################################################################################

df = reading.get_books(fix_names=False)

df = reading.on_shelves(df, [
    'read',
    'currently-reading',
    'pending',
    'elsewhere',
    'ebooks',
])

df1 = reading.ebooks.get_books(fix_names=False)

df = df.append(df1)

authors = sorted(df.Author.unique())

for author in authors:
    try:
        Author(author).fetch_missing()
    except Exception as e:
        print e

Book.save()
Author.save()


# vim: ts=4 : sw=4 : et
