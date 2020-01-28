# vim: ts=4 : sw=4 : et

import pytest

from reading.cmds import arg_parser


def _parse_cmdline(line):
    return arg_parser().parse_args(line.split()[1:])


def _parse_bad_cmdline(line):
    with pytest.raises(SystemExit):
        _parse_cmdline(line)


def test_arg_parser():
    assert arg_parser(), 'got something'

    # test various commands (a) parse, (b) look vaguely sensible

    _parse_bad_cmdline('ook')

    assert _parse_cmdline('ook graph')
    assert _parse_cmdline('ook graph rate')

    assert _parse_cmdline('ook lint')
    assert _parse_cmdline('ook lint borrowed')

    _parse_bad_cmdline('ook config')
    assert _parse_cmdline('ook config goodreads.user')

