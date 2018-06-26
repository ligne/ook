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

author_ids = set(df[df['Author Id'].notnull()]['Author Id'].astype(int).values)
work_ids = set(df[df.Work.notnull()].Work.astype(int).values)

authors = {}

fixes = {}

# search doesn't work at all well with non-english books...
for ix, book in df[df.Language == 'en'].sample(frac=1).iterrows():
    metadata = book.rename({
        'Author Id': 'AuthorId',
    }).fillna('').to_dict()

    if not metadata['Work']:
        print("Searching for '{}' by '{}'".format(metadata['Title'], metadata['Author']))
        resp = lookup_work_id(metadata, author_ids, work_ids)
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
            print(metadata['AuthorId'], metadata['Work'])
            author_ids.add(int(metadata['AuthorId']))
            work_ids.add(int(metadata['Work']))

    df.loc[ix,'Work'] = metadata['Work']
    df.loc[ix,'Author Id'] = metadata['AuthorId']
    authors[metadata['AuthorId']] = metadata['Author']

    # save the caches


Collection(df=df).save()

print(authors)

# vim: ts=4 : sw=4 : et
