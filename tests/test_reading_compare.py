# vim: ts=4 : sw=4 : et

from nose.tools import *
from io import StringIO

from reading.collection import Collection

import reading.compare


# converts a CSV fragment into books
def _to_books(csv):
    header = "Book Id,Added,Author,Author Id,AvgRating,Binding,Borrowed,Category,Entry,Language,Pages,Published,Rating,Read,Scheduled,Series,Series Id,Shelf,Started,Title,Work\n"
    c = Collection(gr_csv=StringIO(header + csv))
    return (x.fillna('') for x in (c.df.iloc[0], c.df.iloc[1]))

################################################################################


def test_compare():
    pass


def test__added():
    b1, b2 = _to_books(
"""
26570162,2017-07-27,Matthew Lewis,7798465,3.8,Paperback,False,novels,,en,339,1796,0,,,,,pending,,The Monk,3095060
23533039,2016-10-31,Ann Leckie,3365457,4.2,Paperback,False,novels,3,en,330,2015,0,,,Imperial Radch,113751,pending,,Ancillary Mercy,43134689
""")

    assert_multi_line_equal(reading.compare._added(b1), """
Added The Monk by Matthew Lewis to shelf 'pending'
  * novels
  * 339 pages
  * Language: en
""".strip())

    assert_multi_line_equal(reading.compare._added(b2), """
Added Ancillary Mercy by Ann Leckie to shelf 'pending'
  * Imperial Radch series, Book 3
  * novels
  * 330 pages
  * Language: en
""".strip())


def test__removed():
    c = Collection(gr_csv=StringIO("""
Book Id,Added,Author,Author Id,AvgRating,Binding,Borrowed,Category,Entry,Language,Pages,Published,Rating,Read,Scheduled,Series,Series Id,Shelf,Started,Title,Work
26570162,2017-07-27,Matthew Lewis,7798465,3.8,Paperback,False,novels,,en,339,1796,0,,,,,pending,,The Monk,3095060
"""))

    assert_multi_line_equal(reading.compare._removed(c.df.iloc[0]), """
Removed The Monk by Matthew Lewis from shelf 'pending'
""".strip())


def test__changed():
    old, new = _to_books(
"""
20636970,2017-02-07,Émile Zola,4750,3.83,Paperback,False,novels,2,fr,380,1872,3,2018-03-14,,Les Rougon-Macquart,40441,read,2017-12-28,La Curée,839934
20636970,2017-02-07,Émile Zola,4750,3.83,Paperback,False,novels,2,fr,380,1872,3,2018-03-14,,Les Rougon-Macquart,40441,read,2017-12-28,La Curée,839934
""")

    # FIXME should do nothing if they're both equal?
    eq_(reading.compare._changed(old, new), None)

    ####

    # changed name and title are treated specially
    old, new = _to_books(
"""
20636970,2017-02-07,Émile zola,4750,3.83,Paperback,False,novels,2,fr,380,1872,3,2018-03-14,,Les Rougon-Macquart,40441,read,2017-12-28,La Curée,839934
20636970,2017-02-07,Émile Zola,4750,3.83,Paperback,False,novels,2,fr,380,1872,3,2018-03-14,,Les Rougon-Macquart,40441,read,2017-12-28,La Curée,839934
""")

    assert_multi_line_equal(reading.compare._changed(old, new), """
Émile Zola, La Curée
  * Author changed from 'Émile zola'
""".strip())

    ####

    old, new = _to_books(
"""
20636970,2017-02-07,Émile Zola,4750,3.83,Paperback,False,novels,2,fr,380,1872,3,2018-03-14,,Les Rougon-Macquart,40441,read,2017-12-28,Le Curée,839934
20636970,2017-02-07,Émile Zola,4750,3.83,Paperback,False,novels,2,fr,380,1872,3,2018-03-14,,Les Rougon-Macquart,40441,read,2017-12-28,La Curée,839934
""")

    assert_multi_line_equal(reading.compare._changed(old, new), """
Émile Zola, La Curée
  * Title changed from 'Le Curée'
""".strip())

    ####

    # various other fields changed
    old, new = _to_books(
"""
34232174,2017-12-26,Helen Dunmore,41542,3.72,Paperback,True,novels,,en,416,2017,0,,,,,elsewhere,,Birdcage Walk,51949108
34232174,2017-12-26,Helen Dunmore,41542,3.72,Paperback,True,novels,,en,426,2017,0,,,,,pending,,Birdcage Walk,51949108
""")

    assert_multi_line_equal(reading.compare._changed(old, new), '''
Helen Dunmore, Birdcage Walk
  * Shelf: elsewhere → pending
  * Pages: 416 → 426
'''.strip())

    ####

    # fields set and unset
    old, new = _to_books(
"""
34232174,2017-12-26,Helen Dunmore,41542,3.72,,True,novels,,en,416,2017,0,,,,,elsewhere,,Birdcage Walk,51949108
34232174,2017-12-25,Helen Dunmore,41542,3.72,Paperback,True,,,en,426,2017,0,,,,,pending,,Birdcage Walk,51949108
""")

    assert_multi_line_equal(reading.compare._changed(old, new), '''
Helen Dunmore, Birdcage Walk
  * Shelf: elsewhere → pending
  * Category unset (previously novels)
  * Pages: 416 → 426
  * Added: 2017-12-26 → 2017-12-25
  * Binding set to Paperback
'''.strip())

    old, new = _to_books(
"""
34232174,2017-12-25,Helen Dunmore,41542,3.72,Paperback,True,,,en,,2017,0,,,,,pending,,Birdcage Walk,51949108
34232174,2017-12-25,Helen Dunmore,41542,3.72,Paperback,True,,,en,426,2017,0,,,,,pending,,Birdcage Walk,51949108
""")

    assert_multi_line_equal(reading.compare._changed(old, new), '''
Helen Dunmore, Birdcage Walk
  * Pages set to 426
'''.strip())

    ####

    # acquired a book
    old, new = _to_books(
"""
14281,2016-08-25,Alice Munro,6410,4.29,Paperback,False,short-stories,,en,688,1985,0,,,,,to-read,,Selected Stories,351589
25689,2018-06-12,Alice Munro,6410,4.29,Paperback,False,short-stories,,en,412,1985,0,,,,,pending,,Selected Stories,351589
""")

    assert_multi_line_equal(reading.compare._changed(old, new), '''
Alice Munro, Selected Stories
  * Shelf: to-read → pending
  * Pages: 688 → 412
  * Added: 2016-08-25 → 2018-06-12
'''.strip())


def test__started():
    c = Collection(gr_csv=StringIO("""
Book Id,Added,Author,Author Id,AvgRating,Binding,Borrowed,Category,Entry,Language,Pages,Published,Rating,Read,Scheduled,Series,Series Id,Shelf,Started,Title,Work
8899970,2018-02-24,Graham Greene,2533,3.66,Paperback,False,novels,,en,190,1936,4,,,,,currently-reading,2018-03-05,A Gun for Sale,151810
"""))

    assert_multi_line_equal(reading.compare._started(c.df.iloc[0]), """
Started A Gun for Sale by Graham Greene
  * 190 pages
""".strip())


def test__finished():
    c = Collection(gr_csv=StringIO("""
Book Id,Added,Author,Author Id,AvgRating,Binding,Borrowed,Category,Entry,Language,Pages,Published,Rating,Read,Scheduled,Series,Series Id,Shelf,Started,Title,Work
491030,2016-04-18,Iain Banks,7628,3.84,Paperback,False,novels,,en,288,1986,4,2016-08-10,,,,read,2016-07-19,The Bridge,1494168
"""))

    assert_multi_line_equal(reading.compare._finished(c.df.iloc[0]), """
Finished The Bridge by Iain Banks
  2016-07-19 → 2016-08-10 (22 days)
  288 pages, 13 pages/day
  Rating: 4
""".strip())

