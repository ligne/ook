# vim: ts=4 : sw=4 : et

from nose.tools import *

from reading.metadata import *

import reading.wikidata


def test__list_choices():
#    # nothing
#    assert_multi_line_equal(reading.metadata._list_choices([]), '')
#
#    # a couple of authors
#    assert_multi_line_equal(reading.metadata._list_choices([
#        #reading.wikidata.search('Iain Banks'),
#        { 'QID': 'Q312579',   'Title': 'Iain Banks', 'Description': 'Scottish writer' },
#        { 'QID': 'Q16386218', 'Title': 'Iain Banks bibliography', 'Description': '' },
#    ]), '''
#\033[1m 1.\033[0m Iain Banks
#      Scottish writer
#      https://www.wikidata.org/wiki/Q312579
# 2. Iain Banks bibliography
#      https://www.wikidata.org/wiki/Q16386218
#'''.lstrip())
#
    assert_multi_line_equal.__self__.maxDiff = None
#
#    # books from goodreads title search
#    assert_multi_line_equal(reading.metadata._list_choices([
#        {'Ratings': '31583', 'Published': '1853', 'BookId': '182381', 'Work': '1016559', 'Author': 'Elizabeth Gaskell', 'AuthorId': '1413437', 'Title': 'Cranford'},
#        {'Ratings': '1515', 'Published': '1859', 'BookId': '2141817', 'Work': '21949576', 'Author': 'Elizabeth Gaskell', 'AuthorId': '1413437', 'Title': 'The Cranford Chronicles'},
#        {'Ratings': '74', 'Published': '2009', 'BookId': '7329542', 'Work': '8965360', 'Author': 'Elizabeth Gaskell', 'AuthorId': '1413437', 'Title': 'Return to Cranford: Cranford and other stories'},
#        {'Ratings': '10', 'Published': '2000', 'BookId': '732416', 'Work': '718606', 'Author': 'J.Y.K. Kerr', 'Author Id': '1215308', 'Title': 'Cranford'},
#        {'Ratings': '428', 'Published': '1864', 'BookId': '222401', 'Work': '215385', 'Author': 'Elizabeth Gaskell', 'AuthorId': '1413437', 'Title': 'Cranford/Cousin Phillis'},
#    ]), '''
#\033[1m 1.\033[0m Cranford
#      Elizabeth Gaskell
#      Published: 1853
#      Ratings: 31583
#      https://www.goodreads.com/book/show/182381
# 2. The Cranford Chronicles
#      Elizabeth Gaskell
#      Published: 1859
#      Ratings: 1515
#      https://www.goodreads.com/book/show/2141817
# 3. Return to Cranford: Cranford and other stories
#      Elizabeth Gaskell
#      Published: 2009
#      Ratings: 74
#      https://www.goodreads.com/book/show/7329542
# 4. Cranford
#      J.Y.K. Kerr
#      Published: 2000
#      Ratings: 10
#      https://www.goodreads.com/book/show/732416
# 5. Cranford/Cousin Phillis
#      Elizabeth Gaskell
#      Published: 1864
#      Ratings: 428
#      https://www.goodreads.com/book/show/222401
#'''.lstrip())

    # books from goodreads title search
    results = [
        {'Work': '3298883', 'AuthorId': '5144', 'BookId': '7588', 'Ratings': '109451', 'Published': '1916', 'Author': 'James Joyce', 'Title': 'A Portrait of the Artist as a Young Man'},
        {'Work': '47198830', 'AuthorId': '5144', 'BookId': '23296', 'Ratings': '5733', 'Published': '1914', 'Author': 'James Joyce', 'Title': 'A Portrait of the Artist as a Young Man / Dubliners'},
        {'Work': '7427316', 'AuthorId': '5144', 'BookId': '580717', 'Ratings': '113', 'Published': '1992', 'Author': 'James Joyce', 'Title': 'Dubliners/A Portrait of the Artist As a Young Man/Chamber Music'},
        {'Work': '10692', 'AuthorId': '5677665', 'BookId': '7593', 'Ratings': '12', 'Published': '1964', 'Author': 'Valerie Zimbarro', 'Title': 'A Portrait of the Artist as a Young Man, Notes'},
    ]
    print(reading.metadata._list_choices(results, author_ids=set([5144]), work_ids=set([3298883])))
    assert_multi_line_equal(reading.metadata._list_choices(results, author_ids=set([5144]), work_ids=set([3298883])), '''
\033[1m 1.\033[0m\033[32m A Portrait of the Artist as a Young Man\033[0m\033[33m
      James Joyce\033[0m
      Published: 1916
      Ratings: 109451
      https://www.goodreads.com/book/show/7588
 2. A Portrait of the Artist as a Young Man / Dubliners\033[0m\033[33m
      James Joyce\033[0m
      Published: 1914
      Ratings: 5733
      https://www.goodreads.com/book/show/23296
 3. Dubliners/A Portrait of the Artist As a Young Man/Chamber Music\033[0m\033[33m
      James Joyce\033[0m
      Published: 1992
      Ratings: 113
      https://www.goodreads.com/book/show/580717
 4. A Portrait of the Artist as a Young Man, Notes\033[0m
      Valerie Zimbarro\033[0m
      Published: 1964
      Ratings: 12
      https://www.goodreads.com/book/show/7593
'''.lstrip())
