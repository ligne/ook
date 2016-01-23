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

# cache word-counts
wcs = shelve.open('.wordcounts.pickle')


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
        'file':   os.path.basename(path),
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
        print '\033[32m' + fi['title'] + '\033[00m'
        fh.write('{words}\t{file}\t{title}'.format(**fi))
        if fi['author'] != 'Unknown':
            fh.write(' ({author})'.format(**fi))
        fh.write('\n')


# main

tmpdir = tempfile.mkdtemp() + '/'

for d in 'articles', 'short-stories', 'books':
    with open('{}/{}-lengths.txt'.format(tmpdir, d), 'w') as fh:
        with open('excludes/rsync-excludes-{}'.format(d), 'w') as excludes:
            files = os.walk(d).next()[2]
            for f in files:
                path = d + '/' + f

                ext = 'mobi'
                _ext = os.path.splitext(path)[1]
                if _ext == '.txt':
                    ext = 'txt'
                elif _ext == '.pdf':
                    ext = 'pdf'

                fi = file_infos(path, ext)
                print_entry(fi, fh)
                excludes.write('# {:7d}\t{}\n/{}\n'.format(fi['words'], fi['title'], f))


# reset the colours, because ffs calibre.
sys.stderr.write('\033[0m')

dest = 'wordcounts/'

# show the diff
subprocess.call(['diff', '-uwr', dest, tmpdir])

# move the new files into place
subprocess.call(['rsync', '-ha', '--delete', '--remove-source-files', tmpdir, dest])

# vim: ts=4 : sw=4 : et
