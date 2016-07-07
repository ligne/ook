#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, os, glob, subprocess, re, time
import tempfile
import shelve

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
        wcs[path] = [ wordcount(path), metadata(path) ]

    words = wcs[path][0]
    (author, title, language) = [ s.encode('utf-8') for s in wcs[path][1:] ]

    display = display_title(author, title)

    return {
        'title':  title,
        'author': author,
        'words':  words,
        'display': display,
        'language': language,
        'file':   os.path.basename(path),
    }


# returns the wordcount for a document.
def wordcount(path):
    if subprocess.call(['ebook-convert', path, '/tmp/test.txt'], stdout=DEVNULL, stderr=DEVNULL):
        print "something wrong counting words in", path
        return

    words = 0
    with open('/tmp/test.txt', 'r') as book:
        for line in book:
            words += len(line.split(None))

    return words


# returns sanitised versions of the author and title metadata fields.
def metadata(path):
    from calibre.ebooks.metadata.meta import get_metadata

    stream = open(path, 'r+b')

    ext = get_calibre_extension(path)

    try:
        mi = get_metadata(stream, ext, force_read_metadata=True)
    except:
        print "something wrong with", path
        return

    title  = re.sub(r'\n', ' ', re.sub(r'^(the|a|le|la|les) ', '', mi.get('title'), flags=re.I).expandtabs())
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
    if author != 'Unknown':
        fmt = '{}\t{}'
    return fmt.format(title, author)


def format_author(author):
    # strip any obvious dates out
    author = re.sub(r'\d+\??-\d+\??', '', author)

    # strip stuff in brackets out.  FIXME too aggressive.
    author = re.sub(r' \(.+?\)', '', author)

    # reorder
    author = ' '.join([ x for x in reversed(author.split(', ')) if re.search(r'\w', x)])

    # strip/squash unwanted whitespace
    author = re.sub(r'\s+', ' ', author)
    author = author.strip()

    return author


# formats and prints information about a document (if they exist) to
# $filehandle.
def print_entry(fi, filehandle=sys.stdout):
    if fi and fi['words'] is not None:
#        print '\033[32m' + fi['title'] + '\033[00m'
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
def process_dir(category, d):
    files = sorted(os.walk(d).next()[2], key=lambda x: os.path.getmtime(d + '/' + x))
    for f in files:
        if f == 'My Clippings.txt':
            continue

        path = d + '/' + f

        fi = file_infos(path)

        fh = get_filehandle(wordcounts_tmpdir, category, fi['language'])
        print_entry(fi, fh)


if __name__ == "__main__":
    tmpdir = tempfile.mkdtemp() + '/'
    wordcounts_tmpdir = tmpdir + 'wordcounts/'

    os.mkdir(wordcounts_tmpdir)

    for d in 'articles', 'short-stories', 'books', 'non-fiction':
        path = os.environ['HOME'] + '/.kindle/documents/' + d
        process_dir(d, path)

    process_dir('articles', os.environ['HOME'] + '/.kindle/documents/')

    close_filehandles()

    # reset the colours, because ffs calibre.
    sys.stderr.write('\033[0m')

    show_update(wordcounts_tmpdir, 'wordcounts/')

# vim: ts=4 : sw=4 : et
