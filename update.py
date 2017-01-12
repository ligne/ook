#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, os
import tempfile
import subprocess
import re

import reading.ebooks


default_categories = [
    'books',
    'short-stories',
    'non-fiction',
]


kindle_dir = '/run/media/mlb/Kindle/'
backup_dir = '/home/local/mlb/.kindle/'
exclude_file = os.environ['HOME'] + '/.kindle-excludes'


if not os.path.isdir(kindle_dir):
    print "Kindle not mounted"
    sys.exit(1)

os.chdir(os.environ['HOME'] + '/ebooks')

# clean up cruft
subprocess.call(['./clean.py'])
# echo

# copy any new files over
# FIXME nothing to do here yet

# take a backup
subprocess.call(['rsync', '-ha', '--delete', '--exclude-from', exclude_file, kindle_dir, backup_dir])

# recalculate wordcounts
subprocess.call(['./wordcounts.py'])

# regenerate the graphs and update the total ebook wordcount
subprocess.call(['./reading.py'])


tmpdir = tempfile.mkdtemp()
print tmpdir

# # update suggestions
# (
#   echo All Books
#   echo
#   ./suggestions.py wordcounts/books-*-lengths.txt 15
#   echo ----
#   echo All short stories
#   echo
#   ./suggestions.py wordcounts/short-stories-*-lengths.txt 15
#   echo ----
#   echo French books
#   echo
#   ./suggestions.py wordcounts/*-fr-lengths.txt 15
#   echo ----
#   echo Non-fiction
#   echo
#   ./suggestions.py wordcounts/non-fiction-*-lengths.txt 15
# ) | cut -c-50 > $tmpdir/00\ Suggestions.txt


# add alphabetically and numerically sorted versions of all wordcount lists.

# print out rows in $df, with a maximum line length.
def print_section(header, df, fh=sys.stdout):
    print >>fh, header
    print >>fh, ''
    for ix, row in df.iterrows():
        fmt = '{Words:7.0f}  {Title}'
        if row['Author']:
            fmt += ' ({Author})'
        print >>fh, '{:.50s}'.format(fmt.format(**row))

    print >>fh, '----'


with open(tmpdir + '/00 Numeric.txt', 'w') as numeric, open(tmpdir + '/00 Alphabetical.txt', 'w') as alpha:
    # for each combination
    combinations = [
        [ 'Articles', ['articles'], []],
        [ 'Novels', ['books'], []],
        [ 'Short stories', ['short-stories'], []],
        [ 'Non-fiction', ['non-fiction'], []],
        [ 'English', [], ['en']],
        [ 'French', [], ['fr']],
        [ 'Everything', [], []],
    ]

    for (t, c, l) in combinations:
        df = reading.get_books(shelves=['kindle'], **{'categories': c, 'languages': l})

        # numeric
        print_section(t, df.sort('Words', ascending=False), numeric)

        # alphabetical
        df['alpha'] = df['Title'].apply(lambda x:
            re.sub(r'^(the|a|le|la|les) ', '', x, flags=re.I).lower()
        )
        print_section(t, df.sort('alpha'), alpha)


# diff -uwr $kindle_dir/documents/wordcounts/00\ Suggestions.txt $tmpdir/
# rsync -ha --delete $tmpdir/ $kindle_dir/documents/wordcounts/


# vim: ts=4 : sw=4 : et
