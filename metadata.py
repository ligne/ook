#!/usr/bin/python3

import sys
import argparse

import reading.goodreads
import reading.cache
from reading.collection import Collection
from reading.metadata import *

# load the config to get the GR API key.
import yaml
with open('data/config.yml') as fh:
    config = yaml.load(fh)


def add():
    c = Collection()
    df = c.df

    works = reading.cache.load_yaml('works')

    author_ids = set(df[df['AuthorId'].notnull()]['AuthorId'].astype(int).values)
    work_ids = set(df[df.Work.notnull()].Work.astype(int).values)
    work_ids |= set([v['Work'] for v in works.values()])

    # search doesn't work at all well with non-english books...
    for ix, book in df[df.Language == 'en'].fillna('').sample(frac=1).iterrows():
        m = book.to_dict()

        if not m['Work']:
            print("Searching for '{}' by '{}'".format(m['Title'], m['Author']))
            resp = lookup_work_id(m, author_ids, work_ids)
            if resp == 's':
                # on to the next one
                continue
            elif resp == 'q':
                # save and exit
                break
            elif resp == 'Q':
                # no save
                sys.exit()
            else:
                author_ids.add(int(m['AuthorId']))
                work_ids.add(int(m['Work']))

                works[ix] = {k:int(v) for k,v in m.items() if k in [
                    'BookId',
                    'Work',
                ]}

    reading.cache.dump_yaml('works', works)


# fetch all the information about the books
def update():
    works = reading.cache.load_yaml('works')

    for f,w in works.items():
        book = reading.goodreads.fetch_book(w['BookId'])
        # FIXME need to merge?
#         works[f] = book

    reading.cache.dump_yaml('works', works)


# regenerates the metadata based on what has been gathered.
def rebuild():
    NotImplemented


if __name__ == '__main__':
    add()

# vim: ts=4 : sw=4 : et
