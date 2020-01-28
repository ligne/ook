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

    lint = subparsers.add_parser('lint', help='report problems with the collection')
    lint.add_argument('pattern', nargs='?')

    graph = subparsers.add_parser('graph', help='draw graphs')
    graph.add_argument('pattern', nargs='?')

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

    return 0

