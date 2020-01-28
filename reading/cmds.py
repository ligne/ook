# vim: ts=4 : sw=4 : et

import argparse
import datetime
import pandas as pd


def _filter_parser():
    parser = argparse.ArgumentParser(add_help=False)
    # FIXME validate choices
    parser.add_argument('--shelves', nargs='+', default=[
        'pending',
        'elsewhere',
        'ebooks',
        'kindle',
    ])
    parser.add_argument('--languages', nargs='+')
    parser.add_argument('--categories', nargs='+')
    parser.add_argument('--new-authors', action="store_true")
    parser.add_argument('--old-authors', action="store_true")
    parser.add_argument('--new-nationalities', action="store_true")
    parser.add_argument('--old-nationalities', action="store_true")
    parser.add_argument('--borrowed', action='store_true', default=None)

    # miscellaneous
    # FIXME also gender, genre
    # sort
    parser.add_argument('--alpha', action='store_true')
    # display
    parser.add_argument('--size', type=int, default=10)
    parser.add_argument('--all', action="store_true")
    parser.add_argument('--width', type=int, default=None)  # FIXME display option
    parser.add_argument('--words', action="store_true")

    return parser


# returns a parser object
def arg_parser():
    filter_options = _filter_parser()

    # main parser
    parser = argparse.ArgumentParser()

    # common options
    parser.add_argument(
        '--date',
        type=lambda d: datetime.datetime.strptime(d, '%Y-%m-%d'),
        default=pd.Timestamp('today'),
    )
    parser.add_argument('-n', '--ignore-changes', action='store_true')
    parser.add_argument('-f', '--force', action='store_true')

    # output options

    # subparsers
    subparsers = parser.add_subparsers(title='subcommands', dest='mode')
    subparsers.required = True

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

    config = subparsers.add_parser('config', help='display configuration options')
    config.add_argument('key')

    return parser


def main():
    args = arg_parser().parse_args()
    print(args)

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

    return 0

