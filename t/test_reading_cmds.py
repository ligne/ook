# vim: ts=4 : sw=4 : et

from reading.cmds import arg_parser


def _parse_cmdline(line):
    return line.split()[1:]


def test_arg_parser():
    assert arg_parser(), 'got something'

    # test various commands (a) parse, (b) look vaguely sensible

    assert arg_parser().parse_args(_parse_cmdline('ook graph'))
    assert arg_parser().parse_args(_parse_cmdline('ook graph rate'))

    assert arg_parser().parse_args(_parse_cmdline('ook lint'))
    assert arg_parser().parse_args(_parse_cmdline('ook lint borrowed'))

