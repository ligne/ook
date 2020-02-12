# vim: ts=4 : sw=4 : et

from reading.wikidata import _uc_first


def test__uc_first():
    tests = [
        ['test', 'Test'],
        ['Test', 'Test'],
        ['Test', 'Test'],
        ['TEST', 'TEST'],
        ['t', 'T'],
        ['', ''],
    ]

    for string, expected in tests:
        assert _uc_first(string) == expected

