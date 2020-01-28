# vim: ts=4 : sw=4 : et

import argparse


# returns a parser object
def arg_parser():
    parser = argparse.ArgumentParser()

    # common options
    parser.add_argument('-n', '--ignore-changes', action='store_true')
    parser.add_argument('-f', '--force', action='store_true')

    # output options

    # subparsers
    subparsers = parser.add_subparsers(title='subcommands', dest='mode')
    subparsers.required = True

    return parser


def main():
    args = arg_parser().parse_args()
    print(args)

    return 0

