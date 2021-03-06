# vim: ts=4 : sw=4 : et

"""Main entry point for the application. Argument parsing and dispatch."""

import argparse
import pandas as pd

from .config import CATEGORIES, SHELVES


def _filter_parser():
    parser = argparse.ArgumentParser(add_help=False)

    parser.add_argument(
        "--shelves",
        nargs="+",
        choices=SHELVES,
        default=(SHELVES - {"to-read"})
    )
    parser.add_argument("--languages", nargs="+")
    parser.add_argument(
        "--categories",
        nargs="+",
        choices=CATEGORIES,
        default=(CATEGORIES - {"articles"}),
    )
    parser.add_argument('--new-authors', action="store_true")
    parser.add_argument('--old-authors', action="store_true")
    parser.add_argument('--new-nationalities', action="store_true")
    parser.add_argument('--old-nationalities', action="store_true")
    parser.add_argument('--borrowed', action='store_true', default=None)

    # miscellaneous
    # FIXME also gender, genre
    # sort
    parser.add_argument('--alpha', action='store_true')
    parser.add_argument('--age', action='store_true')
    parser.add_argument('--words', action="store_true")
    # display
    parser.add_argument('--size', type=int, default=10)
    parser.add_argument('--all', action="store_true")
    parser.add_argument('--width', type=int, default=None)  # FIXME display option

    return parser


# returns a parser object
def arg_parser():
    filter_options = _filter_parser()

    # main parser
    parser = argparse.ArgumentParser()

    # common options
    parser.add_argument("--date", type=pd.Timestamp, default=pd.Timestamp("today"))
    parser.add_argument('-n', '--ignore-changes', action='store_true')
    parser.add_argument('-f', '--force', action='store_true')

    # output options

    # subparsers
    subparsers = parser.add_subparsers(title='subcommands', dest='mode')
    subparsers.required = True

    update = subparsers.add_parser('update', argument_default=[])
    update.add_argument('--goodreads', dest='update', action='append_const', const='goodreads')
    update.add_argument('--kindle', dest='update', action='append_const', const='kindle')
    update.add_argument('--scrape', dest='update', action='append_const', const='scrape')

    metadata = subparsers.add_parser('metadata')
    metadata_choices = ['books', 'authors']
    metadata.add_argument('--find', nargs='?', const=metadata_choices, choices=metadata_choices)
    # FIXME some way of selecting a particular BookId

    subparsers.add_parser(
        'scheduled',
        parents=[filter_options],
        help='show scheduled books',
    )

    subparsers.add_parser(
        'suggest',
        parents=[filter_options],
        help='suggest books',
    )

    lint = subparsers.add_parser('lint', help='report problems with the collection')
    lint.add_argument('pattern', nargs='?')

    graph = subparsers.add_parser('graph', help='draw graphs')
    graph.add_argument('pattern', nargs='?')

    reports = subparsers.add_parser('reports', help='generate lists of books')
    reports.add_argument('names', nargs='*', help='the pre-configured report to generate')
    # FIXME support custom reports

    config = subparsers.add_parser('config', help='display configuration options')
    config.add_argument('key')

    return parser


def main():
    args = arg_parser().parse_args()

    if args.mode == 'update':
        import reading.update
        reading.update.main(args)
    if args.mode == 'metadata':
        import reading.metadata
        reading.metadata.main(args)
    if args.mode == 'lint':
        import reading.lint
        reading.lint.main(args)
    if args.mode == 'graph':
        import reading.graph
        reading.graph.main(args)
    if args.mode == 'config':
        import reading.config
        reading.config.main(args)
    if args.mode == 'scheduled':
        import reading.suggestions
        reading.suggestions.scheduled(args)  # !
    if args.mode == 'suggest':
        import reading.suggestions
        reading.suggestions.main(args)
    if args.mode == 'reports':
        import reading.reports
        reading.reports.main(args)

    return 0

