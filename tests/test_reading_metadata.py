# vim: ts=4 : sw=4 : et

from nose.tools import *

from reading.metadata import *

import reading.wikidata


def test__list_choices():
    # nothing
    assert_multi_line_equal(reading.metadata._list_choices([]), '')

    # a couple of authors
    assert_multi_line_equal(reading.metadata._list_choices([
        #reading.wikidata.search('Iain Banks'),
        { 'QID': 'Q312579',   'Title': 'Iain Banks', 'Description': 'Scottish writer' },
        { 'QID': 'Q16386218', 'Title': 'Iain Banks bibliography', 'Description': '' },
    ]), '''
\033[1m 1.\033[0m Iain Banks
      Scottish writer
      https://www.wikidata.org/wiki/Q312579
 2. Iain Banks bibliography
      https://www.wikidata.org/wiki/Q16386218
'''.lstrip())

