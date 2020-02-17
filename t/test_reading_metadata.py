# vim: ts=4 : sw=4 : et

import reading.metadata


def test__list_book_choices():
    # nothing
    assert reading.metadata._list_book_choices([], set(), set()) == ''

    # books from goodreads title search
    assert reading.metadata._list_book_choices([
        {
            'Ratings': '31583',
            'Published': '1853',
            'BookId': '182381',
            'Work': '1016559',
            'Author': 'Elizabeth Gaskell',
            'AuthorId': '1413437',
            'Title': 'Cranford'
        }, {
            'Ratings': '1515',
            'Published': '1859',
            'BookId': '2141817',
            'Work': '21949576',
            'Author': 'Elizabeth Gaskell',
            'AuthorId': '1413437',
            'Title': 'The Cranford Chronicles'
        }, {
            'Ratings': '74',
            'Published': '2009',
            'BookId': '7329542',
            'Work': '8965360',
            'Author': 'Elizabeth Gaskell',
            'AuthorId': '1413437',
            'Title': 'Return to Cranford: Cranford and other stories'
        }, {
            'Ratings': '10',
            'Published': '2000',
            'BookId': '732416',
            'Work': '718606',
            'Author': 'J.Y.K. Kerr',
            'AuthorId': '1215308',
            'Title': 'Cranford'
        }, {
            'Ratings': '428',
            'Published': '1864',
            'BookId': '222401',
            'Work': '215385',
            'Author': 'Elizabeth Gaskell',
            'AuthorId': '1413437',
            'Title': 'Cranford/Cousin Phillis'
        }
    ], set(), set()) == '''
\033[1m 1.\033[0m Cranford\033[0m
      Elizabeth Gaskell\033[0m
      Published: 1853
      Ratings: 31583
      https://www.goodreads.com/book/show/182381
      https://www.goodreads.com/author/show/1413437
 2. The Cranford Chronicles\033[0m
      Elizabeth Gaskell\033[0m
      Published: 1859
      Ratings: 1515
      https://www.goodreads.com/book/show/2141817
      https://www.goodreads.com/author/show/1413437
 3. Return to Cranford: Cranford and other stories\033[0m
      Elizabeth Gaskell\033[0m
      Published: 2009
      Ratings: 74
      https://www.goodreads.com/book/show/7329542
      https://www.goodreads.com/author/show/1413437
 4. Cranford\033[0m
      J.Y.K. Kerr\033[0m
      Published: 2000
      Ratings: 10
      https://www.goodreads.com/book/show/732416
      https://www.goodreads.com/author/show/1215308
 5. Cranford/Cousin Phillis\033[0m
      Elizabeth Gaskell\033[0m
      Published: 1864
      Ratings: 428
      https://www.goodreads.com/book/show/222401
      https://www.goodreads.com/author/show/1413437
'''.lstrip()

    # it's both an author and a work that i have already.
    results = [
        {
            'Work': '3298883',
            'AuthorId': '5144',
            'BookId': '7588',
            'Ratings': '109451',
            'Published': '1916',
            'Author': 'James Joyce',
            'Title': 'A Portrait of the Artist as a Young Man'
        }, {
            'Work': '47198830',
            'AuthorId': '5144',
            'BookId': '23296',
            'Ratings': '5733',
            'Published': '1914',
            'Author': 'James Joyce',
            'Title': 'A Portrait of the Artist as a Young Man / Dubliners'
        }, {
            'Work': '7427316',
            'AuthorId': '5144',
            'BookId': '580717',
            'Ratings': '113',
            'Published': '1992',
            'Author': 'James Joyce',
            'Title': 'Dubliners/A Portrait of the Artist As a Young Man/Chamber Music'
        }, {
            'Work': '10692',
            'AuthorId': '5677665',
            'BookId': '7593',
            'Ratings': '12',
            'Published': '1964',
            'Author': 'Valerie Zimbarro',
            'Title': 'A Portrait of the Artist as a Young Man, Notes'
        },
    ]
    assert reading.metadata._list_book_choices(results, author_ids={5144}, work_ids={3298883}) == '''
\033[1m 1.\033[0m\033[32m A Portrait of the Artist as a Young Man\033[0m\033[33m
      James Joyce\033[0m
      Published: 1916
      Ratings: 109451
      https://www.goodreads.com/book/show/7588
      https://www.goodreads.com/author/show/5144
 2. A Portrait of the Artist as a Young Man / Dubliners\033[0m\033[33m
      James Joyce\033[0m
      Published: 1914
      Ratings: 5733
      https://www.goodreads.com/book/show/23296
      https://www.goodreads.com/author/show/5144
 3. Dubliners/A Portrait of the Artist As a Young Man/Chamber Music\033[0m\033[33m
      James Joyce\033[0m
      Published: 1992
      Ratings: 113
      https://www.goodreads.com/book/show/580717
      https://www.goodreads.com/author/show/5144
 4. A Portrait of the Artist as a Young Man, Notes\033[0m
      Valerie Zimbarro\033[0m
      Published: 1964
      Ratings: 12
      https://www.goodreads.com/book/show/7593
      https://www.goodreads.com/author/show/5677665
'''.lstrip()

    # known author, but new book
    results = [
        {
            'Work': '3298883',
            'AuthorId': '5144',
            'BookId': '7588',
            'Ratings': '109451',
            'Published': '1916',
            'Author': 'James Joyce',
            'Title': 'A Portrait of the Artist as a Young Man'
        }, {
            'Work': '47198830',
            'AuthorId': '5144',
            'BookId': '23296',
            'Ratings': '5733',
            'Published': '1914',
            'Author': 'James Joyce',
            'Title': 'A Portrait of the Artist as a Young Man / Dubliners'
        }, {
            'Work': '7427316',
            'AuthorId': '5144',
            'BookId': '580717',
            'Ratings': '113',
            'Published': '1992',
            'Author': 'James Joyce',
            'Title': 'Dubliners/A Portrait of the Artist As a Young Man/Chamber Music'
        }, {
            'Work': '10692',
            'AuthorId': '5677665',
            'BookId': '7593',
            'Ratings': '12',
            'Published': '1964',
            'Author': 'Valerie Zimbarro',
            'Title': 'A Portrait of the Artist as a Young Man, Notes'
        },
    ]
    assert reading.metadata._list_book_choices(results, author_ids={5144}, work_ids=set()) == '''
\033[1m 1.\033[0m A Portrait of the Artist as a Young Man\033[0m\033[33m
      James Joyce\033[0m
      Published: 1916
      Ratings: 109451
      https://www.goodreads.com/book/show/7588
      https://www.goodreads.com/author/show/5144
 2. A Portrait of the Artist as a Young Man / Dubliners\033[0m\033[33m
      James Joyce\033[0m
      Published: 1914
      Ratings: 5733
      https://www.goodreads.com/book/show/23296
      https://www.goodreads.com/author/show/5144
 3. Dubliners/A Portrait of the Artist As a Young Man/Chamber Music\033[0m\033[33m
      James Joyce\033[0m
      Published: 1992
      Ratings: 113
      https://www.goodreads.com/book/show/580717
      https://www.goodreads.com/author/show/5144
 4. A Portrait of the Artist as a Young Man, Notes\033[0m
      Valerie Zimbarro\033[0m
      Published: 1964
      Ratings: 12
      https://www.goodreads.com/book/show/7593
      https://www.goodreads.com/author/show/5677665
'''.lstrip()

