#!/usr/bin/python3

import sys
import argparse
import pandas as pd
import re
from collections import ChainMap

import reading.goodreads
import reading.cache
from reading.collection import Collection
from reading.metadata import *
from reading.compare import compare


# load the config to get the GR API key.
import yaml
with open('data/config.yml') as fh:
    config = yaml.load(fh)


def find():
    c = Collection()
    df = c.df

    works = reading.cache.load_yaml('works')

    author_ids = set(df[df['AuthorId'].notnull()]['AuthorId'].astype(int).values)
    author_ids |= set([v['AuthorId'] for v in works.values() if 'AuthorId' in v])

    work_ids = set(df[df.Work.notnull()].Work.astype(int).values)
    work_ids |= set([v['Work'] for v in works.values()])

    # search doesn't work at all well with non-english books...
    for m in df[df.Language == 'en'].fillna('').sample(frac=1).itertuples():
        if not m.Work and not m.Index in works:
            print("\033[1mSearching for '{}' by '{}'\033[0m".format(m.Title, m.Author))
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
                author_ids.add(resp['AuthorId'])
                work_ids.add(resp['Work'])

                works[m.Index] = {k:v for k,v in resp.items() if k in [
                    'BookId',
                    'Work',
                ]}

                works[m.Index].update(reading.goodreads.fetch_book(resp['BookId']))

    reading.cache.dump_yaml('works', works)


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
            'Work': work['Work'],
            'Author': work_first['Author'],
            'Title': re.sub(' \(.+?\)$', '', work_first['Title']),
            'Language': book_first['Language'],
            'Series': work_first['Series'],
            'SeriesId': work_first['SeriesId'],
            'Entry': work_first['Entry'],
            'Published': work_first['Published'],
            'Pages': work_first['Pages'],
        })

    if not args.ignore_changes:
        reading.cache.dump_yaml('metadata', metadata)

    new = Collection()
    new.df.update(pd.DataFrame(metadata).set_index(['BookId']))
    compare(c.df, new.df)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--ignore-changes', action='store_true')
    args = parser.parse_args()

#    find()
    update()
    rebuild(args)


# vim: ts=4 : sw=4 : et
