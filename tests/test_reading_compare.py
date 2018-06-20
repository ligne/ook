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
    c = Collection(gr_csv=StringIO("""
Book Id,Added,Author,Author Id,AvgRating,Binding,Borrowed,Category,Entry,Language,Pages,Published,Rating,Read,Scheduled,Series,Series Id,Shelf,Started,Title,Work
26570162,2017-07-27,Matthew Lewis,7798465,3.8,Paperback,False,novels,,en,339,1796,0,,,,,pending,,The Monk,3095060
"""))

    assert_multi_line_equal(reading.compare._added(c.df.iloc[0]), """
Added The Monk by Matthew Lewis to shelf 'pending'
  * novels
  * 339 pages
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
34232174,2017-12-26,Helen Dunmore,41542,3.72,Paperback,True,novels,,en,416,2017,0,,,,,elsewhere,,Birdcage Walk,51949108
34232174,2017-12-26,Helen Dunmore,41542,3.72,Paperback,True,novels,,en,426,2017,0,,,,,pending,,Birdcage Walk,51949108
""")

    assert_multi_line_equal(reading.compare._changed(old, new), '''
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

