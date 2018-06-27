#!/usr/bin/python3

import sys
import argparse

import reading.goodreads
from reading.collection import Collection
from reading.metadata import *

# load the config to get the GR API key.
import yaml
with open('data/config.yml') as fh:
    config = yaml.load(fh)


c = Collection()
df = c.df.copy()

author_ids = set(df[df['AuthorId'].notnull()]['AuthorId'].astype(int).values)
work_ids = set(df[df.Work.notnull()].Work.astype(int).values)

import reading.cache
works = reading.cache.load_yaml('works')

# search doesn't work at all well with non-english books...
for ix, book in df[df.Language == 'en'].sample(frac=1).iterrows():
    m = book.fillna('').to_dict()

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
            print(m['AuthorId'], m['Work'])
            author_ids.add(int(m['AuthorId']))
            work_ids.add(int(m['Work']))

        df.loc[ix,'Work'] = m['Work']
        works[int(m['Work'])] = {k:v for k,v in m.items() if k in [
            'Author',
            'AuthorId',
            'BookId'
        ]}

reading.cache.dump_yaml('works', works)
Collection(df=df).save()

# vim: ts=4 : sw=4 : et
