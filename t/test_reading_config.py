# vim: ts=4 : sw=4 : et

from reading.config import config


def test_config():
    assert config('goodreads.user'), 'fetched a key that exists'
    assert not config('blah.blah'), '"fetched" a key that does not exist'

