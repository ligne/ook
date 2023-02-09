# vim: ts=4 : sw=4 : et

import datetime
import shlex
from typing import Any

import pandas as pd
import pytest

from reading.cmds import arg_parser


def _parse_cmdline(line: str) -> Any:
    return arg_parser().parse_args(shlex.split(line)[1:])


def _parse_bad_cmdline(line: str) -> None:
    with pytest.raises(SystemExit):
        _parse_cmdline(line)


def test_arg_parser() -> None:
    assert arg_parser(), "got something"

    # test various commands (a) parse, (b) look vaguely sensible

    _parse_bad_cmdline("ook")

    assert _parse_cmdline("ook graph")
    assert _parse_cmdline("ook graph rate")

    assert _parse_cmdline("ook lint")
    assert _parse_cmdline("ook lint borrowed")

    _parse_bad_cmdline("ook config")
    assert _parse_cmdline("ook config goodreads.user")

    assert _parse_cmdline("ook scheduled")
    assert _parse_cmdline("ook scheduled --shelves pending")
    assert _parse_cmdline("ook scheduled --shelves elsewhere library")
    _parse_bad_cmdline("ook scheduled --shelves badshelf")
    assert _parse_cmdline("ook scheduled --borrowed")
    assert _parse_cmdline("ook scheduled --categories novels")
    assert _parse_cmdline("ook scheduled --categories novels short-stories")
    _parse_bad_cmdline("ook scheduled --categories blah")
    assert _parse_cmdline("ook scheduled --languages en de")

    args = _parse_cmdline("ook scheduled")
    assert "articles" not in args.categories

    assert _parse_cmdline("ook reports")  # should fail
    assert _parse_cmdline("ook reports docs")  # check based on pre-defined ones?

    assert _parse_cmdline("ook suggest")
    assert _parse_cmdline("ook suggest --shelves pending")
    assert _parse_cmdline("ook suggest --shelves elsewhere library")
    _parse_bad_cmdline("ook suggest --shelves badshelf")
    assert _parse_cmdline("ook suggest --borrowed")
    assert _parse_cmdline("ook suggest --categories novels")
    assert _parse_cmdline("ook suggest --categories novels short-stories")
    _parse_bad_cmdline("ook suggest --categories blah")
    assert _parse_cmdline("ook suggest --languages en de")

    args = _parse_cmdline("ook suggest")
    assert "articles" not in args.categories


def test_update_args() -> None:
    args = _parse_cmdline("ook update")
    assert args, "Doesn't do very much, but it works"
    assert args.save is True, "save by default"
    assert not args.goodreads
    assert not args.scrape
    assert not args.kindle

    args = _parse_cmdline("ook update -n")
    assert args.save is False, "-n prevents saving"

    args = _parse_cmdline("ook update --goodreads")
    assert args.goodreads, "goodreads is set to be updated"
    assert not args.scrape, "...but scrape is not"
    assert not args.kindle, "...and neither is kindle"

    args = _parse_cmdline("ook update --scrape")
    assert not args.goodreads, "goodreads is not to be updated"
    assert args.scrape, "...but scrape is"

    args = _parse_cmdline("ook update --scrape --goodreads")
    assert args.goodreads, "goodreads is set to be updated"
    assert args.scrape, "...as is scrape..."
    assert not args.kindle, "...but kindle is still not"


def test_metadata_args() -> None:
    args = _parse_cmdline("ook metadata")
    assert args, "Doesn't do very much, but it works"
    assert args.save is True, "save by default"

    args = _parse_cmdline("ook metadata -n")
    assert args.save is False, "-n prevents saving"

    args = _parse_cmdline("ook metadata --find")
    assert args.find == ["books", "authors"]
    args = _parse_cmdline("ook metadata --find authors")
    assert args.find == "authors"
    args = _parse_cmdline("ook metadata --find books")
    assert args.find == "books"
    _parse_bad_cmdline("ook metadata --find blah")


def test_general_options() -> None:
    args = _parse_cmdline("ook --date 2020-01-01 suggest")
    assert isinstance(args.date, pd.Timestamp), "It's automatically pandas-friendly"
    assert f"{args.date:%F}" == "2020-01-01"

    args = _parse_cmdline("ook --date 2022-10-10 suggest")
    assert f"{args.date:%F}" == "2022-10-10"

    args = _parse_cmdline("ook suggest")
    assert args.date.date() == datetime.date.today(), "Defaults to today's date"

    args = _parse_cmdline("ook --date '1st jan 2020' suggest")
    assert str(args.date.date()) == "2020-01-01"
