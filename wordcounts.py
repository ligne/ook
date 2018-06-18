#!/usr/bin/python3

import sys
from subprocess import check_output, call, DEVNULL
import datetime
from pathlib import Path
import tempfile
import yaml
import argparse
import pandas as pd

from reading.collection import Collection
from reading.compare import compare

with open('data/config.yml') as fh:
    config = yaml.load(fh)


# returns the wordcount for a document.
# FIXME trim standard headers/footers?
def wordcount(path):
    # FIXME use tempfile
    try:
        if call(['ebook-convert', str(path), '/tmp/test.txt'], stdout=DEVNULL, stderr=DEVNULL):
            print("something wrong counting words in", path)
            return
    except OSError:
        # ebook-convert probably doesn't exist
        return 0

    words = 0
    with open('/tmp/test.txt', 'r') as book:
        for line in book:
            words += len(line.split())

    return words


# gathers metadata from the ebook.  annoyingly, calibre doesn't support
# Python3, and there aren't many other easy options...
def metadata(path):
    mi = yaml.load(check_output(['python2', '-c', '''
import os, sys, yaml

sys.path.insert(0, '/usr/lib/calibre')
sys.resources_location  = '/usr/share/calibre'
sys.extensions_location = '/usr/lib/calibre/calibre/plugins'

from calibre.ebooks.metadata.meta import get_metadata

path = sys.argv[1]
ext = os.path.splitext(path)[-1][1:]
ext = ext in ['txt', 'pdf'] and ext or 'mobi'
mi = get_metadata(open(path, 'r+b'), ext, force_read_metadata=True)
print(yaml.dump({
    'Title':     mi.get('title'),
    'Authors':   mi.get('authors'),
    'Languages': mi.get('languages'),
}))
''', str(path)]))

    title = mi['Title']
    author = mi['Authors'][0]
    if author == 'Unknown':
        author = ''

    try:
        language = mi['Languages'][0][:2]
    except:
        language = 'en'

    return (author, title, language)


# returns all the interesting-looking files.  FIXME also want to use the files
# in root of the kindle directory
def get_ebooks(kindle_dir):
    ignore_fname = ['My Clippings.txt']
    ignore_ext   = ['.kfx']

    for d in 'articles', 'short-stories', 'books', 'non-fiction':
        category = d == 'books' and 'novels' or d  # FIXME
        for f in (kindle_dir / d).iterdir():
            fname = f.parts[-1]
            if (not f.is_file()
                 or fname[0] == '.'
                 or fname in ignore_fname
                 or f.suffix in ignore_ext):
                continue
            yield (category, f, str(Path(category, fname)))


def process(df, force=False):
    kindle_dir = Path(config['kindle']['directory'])

    ebooks = []

    for (category, path, name) in get_ebooks(kindle_dir):
        if name in df.index:
            ebook = df.loc[name].to_dict()
            ebook['Book Id'] = name
            ebooks.append(ebook)
            continue

        # get the metadata and wordcount
        (author, title, language) = metadata(path)
        words = wordcount(path)

        ebooks.append({
            'Author': author,
            'Title': title,
            'Added': pd.Timestamp(datetime.date.fromtimestamp(path.stat().st_mtime)),
            'Language': language,
            'Category': category,
            'Book Id': name,
            'Words': words,
        })

    return pd.DataFrame(ebooks).set_index('Book Id')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--ignore-changes', action='store_true')
    args = parser.parse_args()

    old = Collection(shelves=['kindle']).df
    new = process(old)

    if not args.ignore_changes:
        new.sort_index().to_csv('data/ebooks.csv', float_format='%g')

    new = new.assign(Work=None, Shelf='kindle')

#     compare(old, new)

# vim: ts=4 : sw=4 : et
