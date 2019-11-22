#!/usr/bin/python3

import sys
import argparse
import pandas as pd
import re
from collections import ChainMap

import reading.goodreads
import reading.cache
from reading.collection import Collection
from reading.metadata import find
from reading.compare import compare


# fetch all the information about the books
def update():
    works = reading.cache.load_yaml('works')

    for f,w in works.items():
        book = reading.goodreads.fetch_book(w['BookId'])
        # FIXME need to merge?
        works[f].update(book)

    reading.cache.dump_yaml('works', works)


# regenerates the metadata based on what has been gathered.
def rebuild(args):
    c = Collection()

    works = reading.cache.load_yaml('works')
    metadata = []

    for book_id, book in c.df.to_dict('index').items():
        if book_id not in works:
            continue
        work = works[book_id]

        similar = c.df[c.df.Work == work['Work']]
        if len(similar):
            work = similar.iloc[0].to_dict()

        work_first = ChainMap(work, book)
        book_first = ChainMap(book, work)

        metadata.append({
            'BookId': book_id,
            'Work': int(work['Work']),
            'Author': work_first['Author'],
            'Title': re.sub(' \(.+?\)$', '', work_first['Title']),
            'Language': book_first['Language'],
            'Series': work_first['Series'],
            'SeriesId': float(work_first['SeriesId']),
            'Entry': work_first['Entry'],
            'Published': float(work_first['Published']),
            'Pages': float(work_first['Pages']),
        })

    if not args.ignore_changes:
        reading.cache.dump_yaml('metadata', metadata)

    new = Collection()
    new.df.update(pd.DataFrame(metadata).set_index(['BookId']))
    compare(c.df, new.df)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--ignore-changes', action='store_true')

    parser.add_argument('--find', action='store_true')
    parser.add_argument('--update', action='store_true')
    args = parser.parse_args()

    if args.find:
        find()
    elif args.update:
        update()
    else:
        rebuild(args)


# vim: ts=4 : sw=4 : et
