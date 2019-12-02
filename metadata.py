#!/usr/bin/python3

import argparse

from reading.collection import Collection
from reading.metadata import find, rebuild
from reading.compare import compare


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--ignore-changes', action='store_true')

    parser.add_argument('--find', action='store_true')
    parser.add_argument('--update', action='store_true')
    args = parser.parse_args()

    old = Collection().df

    if args.find:
        find()
    elif args.update:
        pass

    new = old.copy()
    metadata = rebuild()
    new.update(metadata)
    compare(old, new)

    if not args.ignore_changes:
        metadata.to_csv('data/metadata.csv', float_format='%.20g')


# vim: ts=4 : sw=4 : et
