#!/usr/bin/python3

from subprocess import check_output, call, DEVNULL
from pathlib import Path
import yaml
import argparse
import pandas as pd

from reading.collection import Collection
from reading.compare import compare
from reading.config import config


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
    mi = yaml.safe_load(check_output(['python2', '-c', '''
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
    except (KeyError, IndexError):
        language = 'en'

    return (author, title, language)


def _ignore_item(path):
    ignore_fname = ['My Clippings.txt']
    ignore_ext   = ['.kfx']

    fname = path.parts[-1]
    return (not path.is_file()
            or fname[0] == '.'
            or fname in ignore_fname
            or path.suffix in ignore_ext)


# returns all the interesting-looking files.
def get_ebooks(kindle_dir):
    for d in 'articles', 'short-stories', 'books', 'non-fiction':
        category = d == 'books' and 'novels' or d  # FIXME
        for f in (kindle_dir / d).iterdir():
            if _ignore_item(f):
                continue
            yield (category, f, str(Path(category, f.parts[-1])))

    for f in kindle_dir.iterdir():
        if _ignore_item(f):
            continue
        yield ('articles', f, str(Path('articles', f.parts[-1])))


def process(df, force=False):
    kindle_dir = Path(config('kindle.directory'))

    ebooks = []

    for (category, path, name) in get_ebooks(kindle_dir):
        if not force and name in df.index:
            ebook = df.loc[name].to_dict()
            ebook['BookId'] = name
            ebooks.append(ebook)
            continue

        # get the metadata and wordcount
        (author, title, language) = metadata(path)
        words = wordcount(path)

        ebooks.append({
            'BookId': name,
            'Author': author,
            'Title': title,
            'Shelf': 'kindle',
            'Category': category,
            'Language': language,
            'Added': pd.Timestamp(path.stat().st_mtime, unit='s').floor('D'),
            'AuthorId': None,
            'Binding': 'ebook',
            'Work': None,
            'Words': words,
            'Borrowed': False,
        })

    return pd.DataFrame(ebooks).set_index('BookId')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--ignore-changes', action='store_true')
    parser.add_argument('-f', '--force', action='store_true')
    args = parser.parse_args()

    old = Collection(
        shelves=['kindle'],
        categories=['novels', 'short-stories', 'non-fiction', 'articles'],  # FIXME
        metadata=False,
    ).df
    new = process(old, force=args.force)

    if not args.ignore_changes:
        Collection(df=new).save()

    new = new.assign(Work=None, Shelf='kindle')

    compare(old, new, use_work=False)

# vim: ts=4 : sw=4 : et
