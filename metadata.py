#!/usr/bin/python3

import sys
import argparse

import reading.cache
from reading.collection import Collection
from reading.metadata import find, rebuild
from reading.compare import compare


# fetch all the information about the books
def update():
    works = reading.cache.load_yaml('works')

    for f,w in works.items():
        book = reading.goodreads.fetch_book(w['BookId'])
        # FIXME need to merge?
        works[f].update(book)

    reading.cache.dump_yaml('works', works)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--ignore-changes', action='store_true')

    parser.add_argument('--find', action='store_true')
    parser.add_argument('--update', action='store_true')
    args = parser.parse_args()

    old = Collection().df

    if args.find:
        find()
    elif args.update:
        update()

    new = old.copy()
    metadata = rebuild()
    new.update(metadata)
    compare(old, new)

    if not args.ignore_changes:
        metadata.to_csv('data/metadata.csv', float_format='%.20g')


# vim: ts=4 : sw=4 : et
