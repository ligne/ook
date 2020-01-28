# vim: ts=4 : sw=4 : et

from reading.cmds import arg_parser


def _parse_cmdline(line):
    return line.split()


def test_arg_parser():
    assert arg_parser(), 'got something'

    # test various commands (a) parse, (b) look vaguely sensible

