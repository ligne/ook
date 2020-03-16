# vim: ts=4 : sw=4 : et

from subprocess import check_output, call, DEVNULL

from pathlib import Path
from subprocess import CalledProcessError, run
from tempfile import NamedTemporaryFile

import pandas as pd
import yaml

from .config import config


def wordcount(path):
    try:
        if call(['ebook-convert', str(path), '/tmp/test.txt'], stdout=DEVNULL, stderr=DEVNULL):
            print("something wrong counting words in", path)
            return None
    except OSError:
        # ebook-convert probably doesn't exist
        return 0

    words = 0
    with open('/tmp/test.txt', 'r') as book:
        for line in book:
            words += len(line.split())

    return words


# return a file (which may be the original) containing the contents of $path
# as text
def _as_text(path):
    if path.suffix == ".txt":
        return path.read_text()

    tmpfile = NamedTemporaryFile(suffix=".txt")

    try:
        run(["ebook-convert", str(path), tmpfile.name], capture_output=True, check=True)
    except OSError:
        # ebook-convert probably doesn't exist
        return None
    except CalledProcessError as e:
        # it fell over
        print(e)
        return None

    return tmpfile.read()


# counts the words in $textfile. FIXME trim standard headers/footers?
def _count_words(textfile):
    return len(textfile.split()) if textfile is not None else None


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
print(yaml.safe_dump({
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

    return (not path.is_file()
            or path.name[0] == "."
            or path.name in ignore_fname
            or path.suffix in ignore_ext)


# returns all the interesting-looking files.
def get_ebooks(kindle_dir):
    for d in 'articles', 'short-stories', 'books', 'non-fiction':
        category = 'novels' if d == 'books' else d
        for f in (kindle_dir / d).iterdir():
            if _ignore_item(f):
                continue
            yield (category, f, str(Path(category, f.name)))

    for f in kindle_dir.iterdir():
        if _ignore_item(f):
            continue
        yield ("articles", f, str(Path("articles", f.name)))


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
            'Category': category,
            'Language': language,
            'Added': pd.Timestamp(path.stat().st_mtime, unit='s').floor('D'),
            'Words': words,
        })

    return pd.DataFrame(ebooks).set_index('BookId')

