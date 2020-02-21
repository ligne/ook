# vim: ts=4 : sw=4 : et

import datetime
import shlex

import pytest

from reading.cmds import arg_parser


def _parse_cmdline(line):
    return arg_parser().parse_args(shlex.split(line)[1:])


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

    assert _parse_cmdline('ook scheduled')
    assert _parse_cmdline('ook scheduled --shelves pending')
    assert _parse_cmdline("ook scheduled --shelves elsewhere library")
    _parse_bad_cmdline("ook scheduled --shelves badshelf")
    assert _parse_cmdline('ook scheduled --borrowed')
    assert _parse_cmdline('ook scheduled --categories novels')
    assert _parse_cmdline('ook scheduled --categories novels short-stories')
    _parse_bad_cmdline("ook scheduled --categories blah")
    assert _parse_cmdline('ook scheduled --languages en de')

    args = _parse_cmdline("ook scheduled")
    assert "articles" not in args.categories

    assert _parse_cmdline('ook reports')  # should fail
    assert _parse_cmdline('ook reports docs')  # check based on pre-defined ones?

    assert _parse_cmdline('ook suggest')
    assert _parse_cmdline('ook suggest --shelves pending')
    assert _parse_cmdline("ook suggest --shelves elsewhere library")
    _parse_bad_cmdline("ook suggest --shelves badshelf")
    assert _parse_cmdline('ook suggest --borrowed')
    assert _parse_cmdline('ook suggest --categories novels')
    assert _parse_cmdline('ook suggest --categories novels short-stories')
    _parse_bad_cmdline("ook suggest --categories blah")
    assert _parse_cmdline('ook suggest --languages en de')

    args = _parse_cmdline("ook suggest")
    assert "articles" not in args.categories

    assert _parse_cmdline('ook update'), "Doesn't do very much, but it works"
    assert _parse_cmdline('ook update --goodreads')
    assert _parse_cmdline('ook update --scrape')
    assert _parse_cmdline('ook update --scrape --goodreads')
    # FIXME check that the right variables are set?

    assert _parse_cmdline('ook metadata')
    args = _parse_cmdline('ook metadata --find')
    assert args.find == ['books', 'authors']
    args = _parse_cmdline('ook metadata --find authors')
    assert args.find == 'authors'
    args = _parse_cmdline('ook metadata --find books')
    assert args.find == 'books'
    _parse_bad_cmdline('ook metadata --find blah')

    # general options

    args = _parse_cmdline('ook --date 2020-01-01 suggest')
    assert str(args.date.date()) == '2020-01-01'

    args = _parse_cmdline('ook --date 2022-10-10 suggest')
    assert str(args.date.date()) == '2022-10-10'

    args = _parse_cmdline("ook suggest")
    assert args.date.date() == datetime.date.today(), "Defaults to today's date"

    args = _parse_cmdline("ook --date '1st jan 2020' suggest")
    assert str(args.date.date()) == '2020-01-01'
