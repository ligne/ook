#!/usr/bin/python

import sys, os, glob, subprocess, re, time
import tempfile
import shelve
import json
import hashlib

sys.path.insert(0, '/usr/lib64/calibre')
sys.resources_location = os.environ.get('CALIBRE_RESOURCES_PATH', '/usr/share/calibre')
sys.extensions_location = os.environ.get('CALIBRE_EXTENSIONS_PATH', '/usr/lib64/calibre/calibre/plugins')
sys.executables_location = os.environ.get('CALIBRE_EXECUTABLES_PATH', '/usr/bin')

from calibre.ebooks.metadata.meta import get_metadata


### some basic initialisation

DEVNULL = open(os.devnull, 'w')

# open the collections
coll = {}
try:
    with open(os.environ['HOME'] + '/.kindle/system/collections.json') as c:
        coll = json.load(c)
except:
    pass

# cache word-counts
wcs = shelve.open(os.environ['HOME'] + '/.wordcounts.pickle')


### Functions and stuff

# returns the wordcount, author and title for a document.
def file_infos(path, ext):
    if path not in wcs:
        wcs[path] = wordcount(path)
    words = wcs[path]

    author, title = metadata(path, ext)

    return {
        'title':  title,
        'author': author,
        'words':  words,
    }


# returns the wordcount for a document.
def wordcount(path):
    if subprocess.call(['ebook-convert', path, '/tmp/test.txt'], stdout=DEVNULL, stderr=DEVNULL):
        return

    words = 0
    with open('/tmp/test.txt', 'r') as book:
        for line in book:
            words += len(line.split(None))

    return words


# returns sanitised versions of the author and title metadata fields.
def metadata(path, ext):
    stream = open(path, 'r+b')

    try:
        mi = get_metadata(stream, ext, force_read_metadata=True)
    except:
        return

    title  = re.sub(r'\n', ' ', re.sub(r'^(the|a|le|la|les) ', '', mi.get('title'), flags=re.I).expandtabs())
    author = re.sub(r'\n', ' ', mi.get('authors')[0])

    return (author, title)


# formats and prints information about a document (if they exist) to
# $filehandle.
def print_entry(fi, filehandle=sys.stdout):
    if fi and fi['words'] is not None:
#        print '\033[32m' + fi['title'] + '\033[00m'
        fh.write('{words}\t{title}'.format(**fi))
        if fi['author'] != 'Unknown':
            fh.write(' ({author})'.format(**fi))
        fh.write('\n')


# searches for the document in the collections file, and returns the
# appropriate one (if any).  warns if it appears in more than one collection.
def collection_lookup(key, f):
    ret = None
    for n, c in coll.items():
        if key in c['items']:
            cname = re.split(r'@', n, maxsplit=1)
            if ret:
                print "{} is in {} as well as {}".format(f, cname[0], ret)
            ret = cname[0]
    return ret


# attempt to get the collection this file is in (if any), through various
# means.
def get_collection(f):
    # hash of the filename
    HASH_PREFIX = "/mnt/us/documents/"
    key = "*%s" % hashlib.sha1("/mnt/us/documents/%s" % os.path.basename(f)).hexdigest()
    c = collection_lookup(key, f)
    if c:  return c

    # documents sent via amazon.
    asin = re.search(r'-asin_([A-Z0-9]+)-type_([A-Z]+)-', f)
    if asin:
        key = '#{}^{}'.format(*asin.groups())
        c = collection_lookup(key, f)
    if c:  return c

    # embedded asin identifier
    stream = open(f, 'r+b')
    try: mi = get_metadata(stream, 'mobi', force_read_metadata=True)
    except: pass
    if mi and mi.has_identifier('mobi-asin'):
        # EBOK suffix
        key = '#{}^{}'.format(mi.get_identifiers()['mobi-asin'], 'EBOK')
        c = collection_lookup(key, f)
        if c:  return c
        # PDOC suffix
        key = '#{}^{}'.format(mi.get_identifiers()['mobi-asin'], 'PDOC')
        c = collection_lookup(key, f)

    return c


# main

d = tempfile.mkdtemp() + '/'

# books
with open(d + '/book-lengths.txt', 'w') as fh:
    for ext in 'prc', 'mobi', 'txt', 'azw', 'azw3':
        for f in glob.glob(os.environ['HOME'] + '/.kindle/documents/books/*.' + ext):
            c = get_collection(f)
            print_entry(file_infos(f, 'mobi'), fh)

# articles
with open(d + '/article-lengths.txt', 'w') as fh:
    for ext in 'azw', 'azw3':
        for f in glob.glob(os.environ['HOME'] + '/.kindle/documents/*.' + ext):
            c = get_collection(f)
            print_entry(file_infos(f, 'mobi'), fh)

# reset the colours, because ffs calibre.
sys.stderr.write('\033[0m')

dest = os.environ['HOME'] + '/wordcounts/'

# show the diff
subprocess.call(['diff', '-uwr', dest, d])

# move the new files into place
subprocess.call(['rsync', '-ha', '--delete', '--remove-source-files', d, dest])

# vim: ts=4 : sw=4 : et
