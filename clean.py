#!/usr/bin/python3

# flake8: noqa
# pylint: skip-file

import glob
import pipes  # used for shell escapes

kindle_dir = '/media/mlb/Kindle/documents/'

dirs = [
    '',
    'articles/',
    'books/',
    'non-fiction/',
    'short-stories/',
]


def clean_files(d):
    for item in glob.glob(d + '*.sdr/'):
        head, sep, tail = item.partition('.sdr/')

        head = head.replace('[', '[[]')

        cruft = True

        for f in glob.glob(head + '.*'):
            if f.endswith('.sdr'):
                continue
            else:
                cruft = False

        if cruft:
            print('rm -r {}'.format(pipes.quote(item)))


for d in dirs:
    clean_files(kindle_dir + d)


# vim: ts=4 : sw=4 : et
