#!/usr/bin/python

import sys, os, glob, subprocess, re, time
import tempfile
import shelve

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
def file_infos(path):
    if path not in wcs:
        wcs[path] = wordcount(path)
    words = wcs[path]

    author, title = metadata(path)
    display = display_title(author, title)

    return {
        'title':  title,
        'author': author,
        'words':  words,
        'display': display,
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
def metadata(path):
    stream = open(path, 'r+b')

    ext = get_calibre_extension(path)

    try:
        mi = get_metadata(stream, ext, force_read_metadata=True)
    except:
        return

    title  = re.sub(r'\n', ' ', re.sub(r'^(the|a|le|la|les) ', '', mi.get('title'), flags=re.I).expandtabs())
    author = re.sub(r'\n', ' ', mi.get('authors')[0])

    return (author, title)


# formats a title/author string for display
def display_title(author, title):
    fmt = '{}'
    if author != 'Unknown':
        fmt = '{} ({})'
    return fmt.format(title, author)


# formats and prints information about a document (if they exist) to
# $filehandle.
def print_entry(fi, filehandle=sys.stdout):
    if fi and fi['words'] is not None:
        print '\033[32m' + fi['title'] + '\033[00m'
        fh.write('{words}\t{file}\t{display}\n'.format(**fi))


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


# main

tmpdir = tempfile.mkdtemp() + '/'
wordcounts_tmpdir = tmpdir + 'wordcounts/'
excludes_tmpdir   = tmpdir + 'excludes/'

os.mkdir(wordcounts_tmpdir)
os.mkdir(excludes_tmpdir)

for d in 'articles', 'short-stories', 'books':
    with open('{}/{}-lengths.txt'.format(wordcounts_tmpdir, d), 'w') as fh:
        with open('{}/{}'.format(excludes_tmpdir, d), 'w') as excludes:
            files = os.walk(d).next()[2]
            for f in files:
                path = d + '/' + f

                fi = file_infos(path)
                print_entry(fi, fh)
                excludes.write('# {}\n/{}\n'.format(fi['display'], f))


# reset the colours, because ffs calibre.
sys.stderr.write('\033[0m')

show_update(wordcounts_tmpdir, 'wordcounts/')
show_update(excludes_tmpdir, 'excludes/')

# vim: ts=4 : sw=4 : et
