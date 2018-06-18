#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, os, glob, subprocess, re, time
import tempfile
import shelve
import csv
import datetime

sys.path.insert(0, '/usr/lib64/calibre')
sys.resources_location = os.environ.get('CALIBRE_RESOURCES_PATH', '/usr/share/calibre')
sys.extensions_location = os.environ.get('CALIBRE_EXTENSIONS_PATH', '/usr/lib64/calibre/calibre/plugins')
sys.executables_location = os.environ.get('CALIBRE_EXECUTABLES_PATH', '/usr/bin')


### some basic initialisation

DEVNULL = open(os.devnull, 'w')

# cache word-counts
wcs = shelve.open('.wordcounts.shelve', writeback=True)


### Functions and stuff

# returns the wordcount, author and title for a document.
def file_infos(path):
    if path not in wcs:
        (author, title, language) = metadata(path)
        words = wordcount(path)
        if author == 'Unknown':
            author = ''
        # only cache if there's a wordcount
        if words:
            wcs[path] = [words, author, title, language]
    else:
        words = wcs[path][0]
        (author, title, language) = [s.encode('utf-8') for s in wcs[path][1:]]

    display = display_title(author, title)

    return {
        'title': title,
        'author': author,
        'words': words,
        'display': display,
        'language': language,
        'file': os.path.basename(path),
    }


# returns the wordcount for a document.
def wordcount(path):
    try:
        if subprocess.call(['ebook-convert', path, '/tmp/test.txt'], stdout=DEVNULL, stderr=DEVNULL):
            print "something wrong counting words in", path
            return
    except OSError:
        # ebook-convert probably doesn't exist
        return 0

    words = 0
    with open('/tmp/test.txt', 'r') as book:
        for line in book:
            words += len(line.split(None))

    return words


# returns sanitised versions of the author and title metadata fields.
def metadata(path):
    try:
        from calibre.ebooks.metadata.meta import get_metadata
    except ImportError:
        name = re.sub('_.{32}.azw3$', '', os.path.basename(path))
        return ('', name, 'en')

    stream = open(path, 'r+b')

    ext = get_calibre_extension(path)

    try:
        mi = get_metadata(stream, ext, force_read_metadata=True)
    except:
        print "something wrong with", path
        return

    title = format_title(mi.get('title'))
    author = re.sub(r'\n', ' ', mi.get('authors')[0])
    author = format_author(author)

    l = mi.get('languages')
    language = 'en'
    if l:
        language = l[0][:2]

    return (author, title, language)


# formats a title/author string for display
def display_title(author, title):
    fmt = '{}'
    if author:
        fmt = '{}\t{}'
    return fmt.format(title, author)


def format_author(author):
    # strip any obvious dates out
    author = re.sub(r'\d+\??-\d+\??', '', author)

    # strip stuff in brackets out.  FIXME too aggressive.
    author = re.sub(r' \(.+?\)', '', author)

    # reorder
    author = ' '.join([x for x in reversed(author.split(', ')) if re.search(r'\w', x)])

    # strip/squash unwanted whitespace
    author = re.sub(r'\s+', ' ', author)
    author = author.strip()

    return author


def format_title(title):
    #title = re.sub(r'\n', ' ', re.sub(r'^(the|a|le|la|les) ', '', title, flags=re.I).expandtabs())
    # clean up whitespace
    title = re.sub(r'\n', ' ', title).expandtabs()
    # remove volume numbers
    title = re.sub(r'Tome [IV]+', '', title)
    title = re.sub(r'Vol(ume|\.) [IV\d]+(?: \(of \d+\))?', '', title)
    title = re.sub(r'tome .*', '', title)

    # remove stray punctuation
    title = re.sub(r'[/ .,]+$', '', title)

    return title


# formats and prints information about a document (if they exist) to
# $filehandle.
def print_entry(fi, filehandle=sys.stdout):
    if fi:
        fi = fi.copy()
        fi['display'] = re.sub(r'^(the|a|le|la|les) ', '', fi['display'], flags=re.I)
        filehandle.write('{words}\t{display}\n'.format(**fi))


# show the differences then move the new files into place
def show_update(source, dest):
    subprocess.call(['diff', '-uwr', dest, source])
    subprocess.call(['rsync', '-ha', '--delete', '--remove-source-files', source, dest])


# returns the filetype for calibre's metadata identification
def get_calibre_extension(path):
    ext = os.path.splitext(path)[1]
    if ext == '.txt':
        return 'txt'
    elif ext == '.pdf':
        return 'pdf'
    else:
        return 'mobi'


# select the right filehandle for a particular file
fhs = {}

def get_filehandle(tmpdir, category, language='en'):
    if (category, language) not in fhs:
        fhs[(category, language)] = open('{}/{}-{}-lengths.txt'.format(tmpdir, category, language), 'w')
    return fhs[(category, language)]


def close_filehandles():
    for fh in fhs.values():
        fh.close()


# processes all the files in directory d
def process_dir(category, d, out):
    entries = {}
    for f in os.walk(d).next()[2]:
        if f == 'My Clippings.txt':
            continue

        # calibre can't handle the latest kindle file format.
        if f[-4:] == '.kfx':
            continue

        path = d + '/' + f

        fi = file_infos(path)
        mtime = os.path.getmtime(path)

        #print '\033[32m' + fi['title'] + '\033[00m'

        # don't merge articles
        if category == 'articles':
            entry = path
        else:
            entry = (fi['author'], fi['title'])

        # add together multiple volumes of the same work
        if entry in entries:
            entries[entry][1]['words'] += fi['words']
        else:
            entries[entry] = (mtime, fi)

    for (mtime, fi) in sorted(entries.values(), key=lambda x: x[0]):
        fh = get_filehandle(wordcounts_tmpdir, category, fi['language'])
        print_entry(fi, fh)
        fi['path'] = '{}/{}'.format(category == 'books' and 'novel' or category, fi.get('file'))
        added = datetime.date.fromtimestamp(mtime).isoformat()
        out.writerow([ fi.get(x) for x in ('path', 'words', 'title', 'author', 'language')] + [added, category])


if __name__ == "__main__":
    tmpdir = tempfile.mkdtemp() + '/'
    wordcounts_tmpdir = tmpdir + 'wordcounts/'

    os.mkdir(wordcounts_tmpdir)

    csvfile = '{}/wordcounts.csv'.format(tmpdir)

    with open(csvfile, 'wb') as csvf:
        fieldnames = ['Book Id', 'Words', 'Title', 'Author', 'Language', 'Added', 'Category']
        out = csv.writer(csvf)
        out.writerow(fieldnames)

        for d in 'articles', 'short-stories', 'books', 'non-fiction':
            path = os.environ['HOME'] + '/.kindle/documents/' + d
            process_dir(d, path, out)

        process_dir('articles', os.environ['HOME'] + '/.kindle/documents/', out)

        close_filehandles()

    # reset the colours, because ffs calibre.
    sys.stderr.write('\033[0m')

    show_update(csvfile, 'data/wordcounts.csv')

# vim: ts=4 : sw=4 : et
