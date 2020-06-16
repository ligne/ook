# vim: ts=4 : sw=4 : et

import re

import pytest

from reading.metadata import _list_book_choices, _read_choice, SaveExit, FullExit, rebuild, confirm_author
from reading.storage import load_df, save_df
from reading.wikidata import Entity


def _colour_to_string(colour):
    styles = ["RESET", "BOLD", "FAINT", "ITALIC", "REVERSE"]
    codes = ["BLACK", "RED", "GREEN", "YELLOW", "BLUE", "MAGENTA", "CYAN", "WHITE"]
    effects = {
        "3": "",   # foreground
        "4": "B",  # background
        "9": "BRIGHT"
    }

    if len(colour) == 1:
        return styles[int(colour)]

    effect, code = list(colour)
    return effects[effect] + codes[int(code)]


def _decode_colourspec(match):
    return (
        "<" + ";".join([_colour_to_string(colour) for colour in match.group(1).split(";")]) + ">"
    )


def decode_colour(string):
    return re.sub("\033" + r"\[([0-9;]*)m", _decode_colourspec, string)


def test_decode_colour():
    assert decode_colour("") == ""
    assert decode_colour("blah") == "blah"
    assert decode_colour("\033[0m") == "<RESET>"
    assert decode_colour("blah\033[32m") == "blah<GREEN>"
    assert decode_colour("blah\033[31mbloh\033[34;42m") == "blah<RED>bloh<BLUE;BGREEN>"
    assert decode_colour("\033[94;42m text") == "<BRIGHTBLUE;BGREEN> text"


#################################################################################

def test__list_book_choices():
    # nothing
    assert _list_book_choices([], set(), set()) == ''

    # books from goodreads title search
    assert decode_colour(_list_book_choices([
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
    ], set(), set())) == """\
<BOLD> 1.<RESET> Cranford<RESET>
      Elizabeth Gaskell<RESET>
      Published: 1853
      Ratings: 31583
      https://www.goodreads.com/book/show/182381
      https://www.goodreads.com/author/show/1413437
 2. The Cranford Chronicles<RESET>
      Elizabeth Gaskell<RESET>
      Published: 1859
      Ratings: 1515
      https://www.goodreads.com/book/show/2141817
      https://www.goodreads.com/author/show/1413437
 3. Return to Cranford: Cranford and other stories<RESET>
      Elizabeth Gaskell<RESET>
      Published: 2009
      Ratings: 74
      https://www.goodreads.com/book/show/7329542
      https://www.goodreads.com/author/show/1413437
 4. Cranford<RESET>
      J.Y.K. Kerr<RESET>
      Published: 2000
      Ratings: 10
      https://www.goodreads.com/book/show/732416
      https://www.goodreads.com/author/show/1215308
 5. Cranford/Cousin Phillis<RESET>
      Elizabeth Gaskell<RESET>
      Published: 1864
      Ratings: 428
      https://www.goodreads.com/book/show/222401
      https://www.goodreads.com/author/show/1413437
"""

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
    assert decode_colour(_list_book_choices(results, author_ids={5144}, work_ids={3298883})) == """\
<BOLD> 1.<RESET><GREEN> A Portrait of the Artist as a Young Man<RESET><YELLOW>
      James Joyce<RESET>
      Published: 1916
      Ratings: 109451
      https://www.goodreads.com/book/show/7588
      https://www.goodreads.com/author/show/5144
 2. A Portrait of the Artist as a Young Man / Dubliners<RESET><YELLOW>
      James Joyce<RESET>
      Published: 1914
      Ratings: 5733
      https://www.goodreads.com/book/show/23296
      https://www.goodreads.com/author/show/5144
 3. Dubliners/A Portrait of the Artist As a Young Man/Chamber Music<RESET><YELLOW>
      James Joyce<RESET>
      Published: 1992
      Ratings: 113
      https://www.goodreads.com/book/show/580717
      https://www.goodreads.com/author/show/5144
 4. A Portrait of the Artist as a Young Man, Notes<RESET>
      Valerie Zimbarro<RESET>
      Published: 1964
      Ratings: 12
      https://www.goodreads.com/book/show/7593
      https://www.goodreads.com/author/show/5677665
"""

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
    assert decode_colour(_list_book_choices(results, author_ids={5144}, work_ids=set())) == """\
<BOLD> 1.<RESET> A Portrait of the Artist as a Young Man<RESET><YELLOW>
      James Joyce<RESET>
      Published: 1916
      Ratings: 109451
      https://www.goodreads.com/book/show/7588
      https://www.goodreads.com/author/show/5144
 2. A Portrait of the Artist as a Young Man / Dubliners<RESET><YELLOW>
      James Joyce<RESET>
      Published: 1914
      Ratings: 5733
      https://www.goodreads.com/book/show/23296
      https://www.goodreads.com/author/show/5144
 3. Dubliners/A Portrait of the Artist As a Young Man/Chamber Music<RESET><YELLOW>
      James Joyce<RESET>
      Published: 1992
      Ratings: 113
      https://www.goodreads.com/book/show/580717
      https://www.goodreads.com/author/show/5144
 4. A Portrait of the Artist as a Young Man, Notes<RESET>
      Valerie Zimbarro<RESET>
      Published: 1964
      Ratings: 12
      https://www.goodreads.com/book/show/7593
      https://www.goodreads.com/author/show/5677665
"""


# helper to raise from inside a lambda
def _raise(exception):
    raise exception


def test__read_choice(monkeypatch):
    length = 3

    monkeypatch.setattr("builtins.input", lambda prompt: "1")
    assert _read_choice(length) == "1", "Selected an index"

    monkeypatch.setattr("builtins.input", lambda prompt: "")
    assert _read_choice(length) == "1", "Default index is 1"

    monkeypatch.setattr("builtins.input", lambda prompt: "q")
    with pytest.raises(SaveExit):
        assert _read_choice(length), "Asked to save and quit"

    monkeypatch.setattr("builtins.input", lambda prompt: "Q")
    with pytest.raises(FullExit):
        assert _read_choice(length), "Asked to save and quit"

    monkeypatch.setattr("builtins.input", lambda prompt: "s")
    assert not _read_choice(length), "Skip to the next"

    monkeypatch.setattr("builtins.input", lambda prompt: _raise(EOFError))
    with pytest.raises(SaveExit):
        assert _read_choice(length), "Ctrl-D saves and exits"

    monkeypatch.setattr("builtins.input", lambda prompt: _raise(KeyboardInterrupt))
    with pytest.raises(FullExit):
        assert _read_choice(length), "Ctrl-C exits without saving"

    inputs = (x for x in ["7", "t", "2"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))
    assert _read_choice(length) == "2", "Invalid option"

    inputs = (x for x in ["?", "1"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))
    assert _read_choice(length) == "1", "Request the help message"


def test__read_choice_output(monkeypatch, capsys):
    length = 3

    monkeypatch.setattr("builtins.input", lambda prompt: "1")
    _read_choice(length)
    output = capsys.readouterr()
    assert output.out == ""

    inputs = (x for x in ["?", "1"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))
    _read_choice(length)
    output = capsys.readouterr()
    assert decode_colour(output.out) == """
<BRIGHTRED>1-3 - select

s - skip to the next author
q - save and exit
Q - exit without saving
? - print help<RESET>
""".lstrip()


################################################################################

def test_confirm_author_reject(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda prompt: "n")

    entity = Entity("Q12807")
    author = confirm_author(entity)
    output = capsys.readouterr()
    assert decode_colour(output.out) == """
<GREEN>Umberto Eco: male, it<RESET>

"""
    assert author is None


def test_confirm_author_accept(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda prompt: "y")

    entity = Entity("Q12807")
    author = confirm_author(entity)
    assert author == {
        "QID": "Q12807",
        "Author": "Umberto Eco",
        "Gender": "male",
        "Nationality": "it",
        "Description": "Italian semiotician, essayist, philosopher, literary critic, and novelist",
    }


def test_confirm_author_default_accepts(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda prompt: "")

    entity = Entity("Q12807")
    author = confirm_author(entity)
    assert author["Nationality"] == "it"


################################################################################

# pylint: disable=line-too-long
def test_rebuild(tmp_path, collection):
    books = collection("2019-12-04", metadata=False).df
    works = load_df("books")

    metadata_csv = tmp_path / "metadata.csv"

    save_df("metadata", rebuild(books, works), metadata_csv)

    assert metadata_csv.read_text() == """\
,Author,AuthorId,Title,Work,Series,SeriesId,Entry,Published,Pages
non-fiction/Coleman-Coding-Freedom.mobi,Gabriella Coleman,7452431,,20545577,,,,2012,254
non-fiction/Evangelii Gaudium Apostolic Exho-asin_ESV27ONBP3ZTFH4Q5LLN7ZCMUNBBLE7T-type_PDOC-v_0.azw3,Pope Francis,7034628,Evangelii gaudium: Apostolic Exhortation,27393319,,,,2013,224
non-fiction/Open-Advice.mobi,,5626219,Open Advice,18984207,,,,2012,308
non-fiction/SustainableEnergy-withoutthehotair-DavidJCMacKay.mobi,,117433,Sustainable Energy - Without the Hot Air,4117179,,,,2008,384
non-fiction/art-of-war.mobi,,1771,,3200649,,,,-500,273
non-fiction/controversy.mobi,Arthur Schopenhauer,11682,The Art Of Controversy,2715274,,,,1831,
non-fiction/malay.mobi,Alfred Russel Wallace,32343,,96053,,,,1869,544
non-fiction/pg1015-images.mobi,,61732,The Oregon Trail,2929928,,,,1847,400
non-fiction/pg132-images.mobi,Sun Tzu,1771,,3200649,,,,-500,273
non-fiction/pg1408.mobi,,44057,,1701350,,,,1788,320
non-fiction/pg14154.mobi,,425652,The Tale Of Terror: A Study Of The Gothic Fiction,1475662,,,,1963,200
non-fiction/pg14363-images.mobi,,27180,The Worst Journey in the World,47447,,,,1922,640
non-fiction/pg19468-images.mobi,,362543,,18492740,,,,2007,
non-fiction/pg2009.mobi,,12793,On the Origin of Species by Means of Natural Selection,481941,,,,1859,791
non-fiction/pg3207.mobi,,10122,,680963,,,,1651,736
non-fiction/pg3300.mobi,,14424,,1373762,,,,1776,1264
non-fiction/pg3532.mobi,,50714,,2101404,,,,1922,106
non-fiction/pg36127-images.mobi,Sabine Baring-Gould,4967158,,643901,,,,1868,255
non-fiction/pg3704.mobi,,12793,Voyage of the Beagle,177481,,,,1839,432
non-fiction/pg3755.mobi,,57639,,2548496,,,,1776,104
non-fiction/pg37893-images.mobi,,920026,,20014135,,,,2008,
non-fiction/pg42960-images.mobi,,1707477,,28779403,,,,2013,262
non-fiction/seven.mobi,T.E. Lawrence,2875209,Seven Pillars of Wisdom: A Triumph,56441,,,,1922,784
non-fiction/supernatural.mobi,H.P. Lovecraft,9494,,124218,,,,1927,106
novels/20140201.mobi,,8734,"Gaudy Night (Lord Peter Wimsey, #12)",341789,Lord Peter Wimsey,42773,12,1935,501
novels/9781429915434_mobi.prc,Robert Charles Wilson,27276,"Spin (Spin, #1)",47562,Spin Saga,52279,1,2005,464
novels/9781429966276_mobi.mobi,,23069,Shadow & Claw (The Book of the New Sun #1-2),40575,The Book of the New Sun,41474,1-2 ,1994,413
novels/9781429968409_mobi.mobi,,338705,"Deathless (Leningrad Diptych, #1)",10733651,,,,2011,352
novels/9781466853447_mobi.mobi,Liu Cixin,5780686,The Three-Body Problem (Remembrance of Earth’s Past #1),25696480,Remembrance of Earth's Past,189931,1,2008,399
novels/9781466863934_mobi.prc,,8794,"The Bloodline Feud (The Merchant Princes, #1-2)",24088841,The Merchant Princes,40515,1-2,2013,564
novels/AUTONOMOUS_mobi.mobi,,191888,,48237590,,,,2017,303
novels/A_DARKER_SHADE_OF_MAGIC_MOBI.mobi,V.E. Schwab,7168230,"A Darker Shade of Magic (Shades of Magic, #1)",40098252,Shades of Magic,122142,1,2015,400
novels/A_Fire_Upon_The_Deep_mobi.mobi,,44037,"A Fire Upon the Deep (Zones of Thought, #1)",1253374,Zones of Thought,52585,1,1992,613
novels/Cory_Doctorow_and_Charles_Stross_-_Rapture_of_the_Nerds.mobi,Cory Doctorow,12581,The Rapture of the Nerds,19101112,,,,2012,351
novels/IN_OUR_OWN_WORLDS_mobi.mobi,,2970944,In Our Own Worlds: Four LGBTQ+ Tor.com Novellas,61405231,,,,2018,479
novels/Luna_New_Moon_MOBI.mobi,,25376,Luna: New Moon (Luna #1),43458032,Luna,166174,1,2015,398
novels/ManStor.mobi,,1274802,,2981165,,,,1920,318
novels/Old_Mans_War_mobi.mobi,,4763,"Old Man's War (Old Man's War, #1)",50700,Old Man's War,40789,1,2005,332
novels/THE_COLLAPSING_EMPIRE_mobi.mobi,,4763,"The Collapsing Empire (The Interdependency, #1)",50498420,The Interdependency,202297,1,2017,336
"novels/The Collected Dashiell Hammett - Hammett, Dashiell.mobi",,16927,,44300783,,,,2015,1818
novels/TheQuantumThief_mobi.mobi,,2768002,"The Quantum Thief (Jean le Flambeur, #1)",9886333,Jean le Flambeur,57134,1,2010,336
novels/The_Black_Tides_of_Heaven_MOBI.mobi,J.Y. Yang,7106859,"The Black Tides of Heaven (Tensorate, #1)",53763120,Tensorate,198015,1,2017,236
novels/The_Castle_of_Wolfenbach.mobi,Eliza Parsons,53468,The Castle of Wolfenbach: A German Story,1066862,,,,1793,224
novels/The_Only_Harmless_Great_Thing_MOBI.mobi,,6889348,,55823786,,,,2018,93
novels/TooLikeTheLightning_mobi.mobi,,8132662,"Too Like the Lightning (Terra Ignota, #1)",46061374,Terra Ignota,166200,1,2016,432
"novels/Treasure of the Sierra Madre, The - B. TRAVEN.mobi",B. Traven,32530,,56170,,,,1935,308
novels/accelerando.mobi,,8794,,930555,,,,2005,415
novels/b869w.mobi,Emily Brontë,4191,,1565818,,,,1847,464
novels/castle.mobi,Maria Edgeworth,82939,,898743,,,,1800,87
novels/chandlerr-longgoodbye-00-e.mobi,,1377,"The Long Goodbye (Philip Marlowe, #6)",998106,Philip Marlowe,168991,6,1953,379
novels/d31j.mobi,Daniel Defoe,2007,A Journal of the Plague Year,12755437,,,,1722,336
novels/d31m.mobi,Daniel Defoe,2007,,3214982,,,,1722,242
novels/d31r.mobi,,2007,,604666,Robinson Crusoe,169255,1,1719,320
novels/e42m.mobi,George Eliot,173,,1461747,,,,1871,904
novels/female-quixote.mobi,Charlotte Lennox,107720,,1247757,,,,1752,464
novels/glenarvon.azw3,Caroline Lamb,325484,,585481,,,,1816,448
novels/house.mobi,J. Sheridan Le Fanu,26930,,1022427,,,,1863,
novels/house1.mobi,William Hope Hodgson,51422,,3150114,,,,1908,156
novels/j8p.mobi,James Joyce,5144,,3298883,,,,1916,329
novels/j8u.mobi,James Joyce,5144,,2368224,,,,1922,783
novels/melmoth_the_wanderer.mobi,Charles Robert Maturin,6523516,,200656,,,,1820,659
novels/moving.mobi,Charlotte Perkins Gilman,29527,,6794187,The Herland Trilogy,154994,1,1911,
novels/o79b.mobi,George Orwell,3706,,1171545,,,,1934,376
novels/o79co.mobi,George Orwell,3706,Coming Up for Air,848305,,,,1939,278
novels/o79h.mobi,George Orwell,3706,,2566499,,,,1938,232
novels/pg10812.mobi,,82525,,4632357,,,,1899,
novels/pg110.mobi,,15905,Tess of the D'Urbervilles,3331021,,,,1891,518
novels/pg11323.mobi,,113910,Caleb Williams,189118,,,,1794,384
novels/pg1188.mobi,,6988,,703918,,,,1911,120
novels/pg1298.mobi,,98909,The Virginian: A Horseman of the Plains,3280421,,,,1902,352
novels/pg1300-images.mobi,,18134,Riders of the Purple Sage (Riders of the Purple Sage #1),2663060,Riders of the Purple Sage,205568,1,1912,320
novels/pg1329.mobi,,29974,,923907,,,,1920,274
novels/pg13765.mobi,,9057,,181928,Joseph Rouletabille,59997,1,1907,288
novels/pg13944-images.mobi,,16038,"After London: or, Wild England",905982,,,,1885,
novels/pg13969.mobi,,33546,,2958815,,,,1907,204
novels/pg140.mobi,,23510,,1253187,,,,1906,335
novels/pg14287.mobi,,696805,,1167706,Extraordinary Voyages,269684,12,1865,826
novels/pg1438.mobi,,4012,,3242295,,,,1862,748
novels/pg15493-images.mobi,,141739,The Lancashire Witches,1463059,,,,1854,584
novels/pg155.mobi,,4012,,1044477,,,,1868,528
novels/pg1622-images.mobi,,4012,,591267,,,,1875,348
novels/pg17144.mobi,,497356,,5492297,,,,1907,144
novels/pg1947.mobi,,82608,"Scaramouche (Scaramouche, #1)",1370942,Scaramouche,54637,1,1921,359
novels/pg1951.mobi,Edward Bulwer-Lytton,44512,,1926578,,,,1871,148
novels/pg2014.mobi,,85931,,1901945,,,,1913,224
novels/pg20749-images.mobi,Walter Scott,4345,St. Ronan's Well: The Works of Sir Walter Scott,6550059,,,,1824,
novels/pg20869-images.mobi,"E.E. ""Doc"" Smith",4477395,The Skylark of Space (Skylark #1),1379469,Skylark,54701,1,1928,212
novels/pg211.mobi,,159,,207680,,,,1888,180
novels/pg215.mobi,,1240,,3252320,,,,1903,172
novels/pg2166-images.mobi,H. Rider Haggard,4633123,"King Solomon's Mines (Allan Quatermain, #1)",575986,Allan Quatermain,49580,1,1885,264
novels/pg217.mobi,D.H. Lawrence,17623,,3173046,,,,1913,654
novels/pg21970-images.mobi,,1240,,2741135,,,,1912,98
novels/pg22002-images.mobi,Elizabeth Inchbald,174038,,725963,,,,1791,384
novels/pg24-images.mobi,,881203,"O Pioneers! (Great Plains Trilogy, #1)",467254,Great Plains Trilogy,87826,1,1913,159
novels/pg24353-images.mobi,,3052377,Wired Love: A Romance of Dots and Dashes,6999631,,,,1879,
novels/pg25016.mobi,,33546,,301492,,,,1906,
novels/pg25024-images.mobi,,23001,,21568680,,,,1960,
novels/pg25026-images.mobi,,2799664,Bristol Bells A Story of the Eighteenth Century,12562502,,,,2008,
novels/pg26740.mobi,,3565,,1858012,,,,1890,272
novels/pg26820.mobi,Claire de Duras,39375,,534748,,,,1823,47
novels/pg29257-images.mobi,Ameen Rihani,412840,,14290657,,,,1911,178
novels/pg29752-images.mobi,,4902494,,14393847,,,,2009,
novels/pg3095.mobi,,6988,,11576198,,,,1909,228
novels/pg3171.mobi,,1244,In Defence of Harriet Shelley ,6552340,,,,1897,
novels/pg32.mobi,,29527,,83484,The Herland Trilogy,154994,2.0,1915,147
novels/pg32325-images.mobi,,1244,The Adventures of Huckleberry Finn,1835605,The Adventures of Tom and Huck,220693,2,1884,327
novels/pg3322-images.mobi,,1779542,,1096822,,,,1861,694
novels/pg34204-images.mobi,,1464,La Petite Fadette,1810799,,,,1848,241
novels/pg35.mobi,H.G. Wells,880695,,3234863,,,,1895,118
novels/pg35517.mobi,,33546,The Three Impostors,69007492,,,,1895,196
novels/pg35587.mobi,Thomas Mayne Reid,312934,The Headless Horseman,2576674,,,,1865,368
novels/pg3781.mobi,,6988,,1799384,Fantasy Classics,224680,5,1903,304
novels/pg394.mobi,Elizabeth Gaskell,1413437,,1016559,,,,1853,257
novels/pg40386-images.mobi,,6478378,The Complete Wandering Ghosts,13404177,,,,1911,152
novels/pg421.mobi,,854076,"Kidnapped (David Balfour, #1)",963266,David Balfour,57633,1,1886,288
novels/pg42197-images.mobi,Alfred J. Church,3041852,With the King at Oxford,40342681,,,,1885,88
novels/pg42243.mobi,,66700,,1294759,,,,1936,296
novels/pg42455-images.mobi,,6988,The Mystery of the Sea (Pocket Classics),1848176,,,,1902,300
novels/pg4277.mobi,Richard Henry Dana Jr.,192314,Two Years Before the Mast: A Sailor's Life at Sea,325869,,,,1840,
novels/pg4313.mobi,,4532116,,661046,,,,1893,432
novels/pg447.mobi,,19879,Maggie: A Girl of the Streets,6712095,,,,1893,92
novels/pg4517.mobi,,16,,132919,,,,1911,189
novels/pg4537-images.mobi,Elizabeth Gaskell,1413437,Sylvia's Lovers,867361,,,,1863,484
novels/pg4559.mobi,,224285,,1968812,,,,1894,239
novels/pg4644-images.mobi,,613351,Adventures of Mr. Verdant Green,1262977,,,,1853,
novels/pg48197-images.mobi,,14266369,Hester,867446,,,,1883,468
novels/pg48198-images.mobi,,14266369,Hester,867446,,,,1883,468
novels/pg48199-images.mobi,,14266369,Hester,867446,,,,1883,468
novels/pg5160.mobi,,5158478,,162739,,,,1410,311
novels/pg5164.mobi,,3348,,802628,,,,1897,364
novels/pg5182.mobi,,8136,The Old English Baron,6246192,,,,1777,144
novels/pg524.mobi,H.G. Wells,880695,Ann Veronica,1292577,,,,1909,352
novels/pg543.mobi,,7330,,18537748,,,,1920,454
novels/pg60.mobi,Emmuska Orczy,2893961,,750426,The Scarlet Pimpernel (publication order),168426,1,1905,182
novels/pg652.mobi,,22191,,920095,,,,1759,
novels/pg6709.mobi,,273618,A Strange Manuscript found in a Copper Cylinder,478291,,,,1888,460
novels/pg6838.mobi,,13661,Le Dernier jour d'un condamné,1632537,,,,1829,97
novels/pg7118.mobi,,159,,319546,,,,1897,275
novels/pg7442.mobi,,696805,Michel Strogoff,2549651,Extraordinary Voyages,269684,14,1876,
novels/pg792.mobi,,46594,"Wieland, or, The Transformation",41791728,,,,1798,204
novels/pg796.mobi,,1481537,La Chartreuse De Parme + CD,1378789,,,,1839,
novels/pg805.mobi,,3190,,2520849,,,,1920,288
novels/pg82.mobi,Walter Scott,4345,,1039021,Waverley Novels,142177,5,1819,541
novels/pg8387.mobi,,18317,,3135610,,,,1890,134
novels/pg86-images.mobi,,1244,,2621763,,,,1889,480
novels/pg8743.mobi,,16920716,"Mary Schweidler, the Amber Witch",5031316,,,,1843,
novels/pg913.mobi,Mikhail Lermontov,15538,,166902,,,,1840,185
novels/phillis.mobi,Elizabeth Gaskell,1413437,,2833678,,,,1864,
novels/s848dj.mobi,Robert Louis Stevenson,854076,The Strange Case of Dr. Jekyll and Mr. Hyde,3164921,,,,1886,144
novels/s87d.mobi,Bram Stoker,6988,,3165724,,,,1897,488
novels/s97g.mobi,Jonathan Swift,1831,Gulliver's Travels,2394716,,,,1726,306
novels/she.mobi,H. Rider Haggard,4633123,"She: A History of Adventure (She, #1)",2334644,Ayesha,72235,1,1886,317
novels/sheep.mobi,John Buchan,3073,The Island of Sheep (Richard Hannay #5),1696409,Richard Hannay,56890,5,1936,207
novels/shuten-townlikealice-01-e.mobi,,21477,,276591,,,,1950,359
novels/sister.mobi,Theodore Dreiser,8987,,2437051,,,,1900,580
novels/st-irvyne.mobi,Percy Bysshe Shelley,45882,St. Irvyne,7135418,,,,1811,
novels/tender.mobi,F. Scott Fitzgerald,3190,Tender Is the Night,8272,,,,1934,315
novels/w91md.mobi,Virginia Woolf,6765,,841320,,,,1925,194
novels/wrenpc-beaugeste-00-e.mobi,P.C. Wren,443003,Beau Geste (Beau Geste #1),1666567,Beau Geste,141417,1,1924,
novels/zastrozzi.mobi,Percy Bysshe Shelley,45882,,1212091,,,,1810,117
short-stories/Elephants and Corpses.azw3_6SSY4WWHRJ2IPXWGYOSXTQPZ2QVNDXWS.azw3,,4369922,,45088462,,,,2015,28
short-stories/Hungry Daughters of Starving Mothers_ZDYH4FSC3BOKBYMNKN7U3ZJIBRBQJO6K.azw3,Alyssa Wong,8178928,,83767233,,,,,
short-stories/Les_soirees_de_Medan.pdf,Émile Zola,4750,Les Soirées de Médan,1838632,,,,1973,290
short-stories/PwningTomorrow_EFF_V2.mobi,Dave Maass,5165105,Pwning Tomorrow,48265311,,,,2015,
short-stories/Selkie Stories Are for Losers.azw3_YZG6GPQJLUDTTSP3IREO6OHI3VS674GT.azw3,Sofia Samatar,5258016,,72224597,,,,2013,5
short-stories/The Complete Works of H.P. Lovecraft.mobi,,9494,,16807494,,,,1978,1305
short-stories/Up-and-Coming-Stories-by-the-2016-Campbell-Eligible-Authors-anthology.mobi,S.L. Huang,8057745,,49670253,,,,,3040
short-stories/Wakulla Springs.azw3_YYYISJ45MEIOATD6QCO34HS56T4DA5IG.azw3,Andy Duncan,331704,,26407361,,,,2013,139
short-stories/alchemist.mobi,H.P. Lovecraft,9494,,6926605,,,,1916,10
short-stories/beast.mobi,H.P. Lovecraft,9494,,6815180,,,,1918,11
short-stories/can-such-things-be.mobi,Ambrose Bierce,14403,,1232123,,,,1893,232
short-stories/d54hh.mobi,Charles Dickens,239579,,2472055,,,,1859,126
short-stories/gates.mobi,H.P. Lovecraft,9494,,26651005,,,,1934,48
short-stories/johnson.mobi,H.P. Lovecraft,9494,,24936731,,,,1917,
short-stories/pg1044-images.mobi,,1244,,1031799,,,,1909,153
short-stories/pg10832.mobi,,51422,,335870,,,,1913,192
short-stories/pg1190.mobi,,159,,1566553,,,,1908,
short-stories/pg1210-images.mobi,,35238,,2562781,,,,1904,256
short-stories/pg1289-images.mobi,,239579,,2538067,,,,1998,
short-stories/pg13094.mobi,,8993,Heart of the West (Annotated),1665026,,,,1919,212
short-stories/pg13707.mobi,,7799,Twice-Told Tales,1337429,,,,1837,432
short-stories/pg13848.mobi,Jules Barbey d'Aurevilly,4547067,Les Diaboliques ,1496555,,,,1874,
short-stories/pg1429-images.mobi,,45712,The Garden Party and Other Stories,1698523,,,,1922,159
short-stories/pg14471.mobi,,38840,,1325142,,,,1906,316
short-stories/pg2048-images.mobi,Geoffrey Crayon,14268699,,18197624,,,,1819,
short-stories/pg28636-images.mobi,Elizabeth Gaskell,1413437,"The Grey Woman, And Other Tales",13384361,,,,1865,
short-stories/pg31377-images.mobi,E.T.A. Hoffmann,7267068,,2081541,,,,1814,
short-stories/pg32759-images.mobi,,66700,,1338546,,,,1936,295
short-stories/pg416.mobi,,45645,"Winesburg, Ohio",191520,,,,1919,240
short-stories/pg4514-images.mobi,,16,,557663,,,,1910,208
short-stories/pg512.mobi,,7799,Mosses from an Old Manse,352796,,,,1846,464
short-stories/pg7144.mobi,,35096,,2305818,,,,1896,
short-stories/pg773.mobi,,3565,,46727906,,,,1891,192
short-stories/pg8090.mobi,,7799,,549619,,,,1863,414
short-stories/pg8128-images.mobi,,35238,"In Ghostly Japan: Spooky Stories with the Folklore, Superstitions and Traditions of Old Japan",2187036,,,,1899,258
short-stories/pg8492.mobi,,57739,,52901661,,,,1895,
short-stories/pharaohs.mobi,H.P. Lovecraft,9494,,18482188,,,,1924,54
short-stories/purcell.mobi,J. Sheridan Le Fanu,26930,,73513,,,,1880,241
short-stories/s848mm.mobi,Robert Louis Stevenson,854076,,18343570,,,,1882,304
short-stories/sweet.mobi,H.P. Lovecraft,9494,,18482045,,,,1943,
short-stories/w45cb.mobi,H.G. Wells,880695,The Country of the Blind and Other Science-Fiction Stories,4035114,,,,1909,90
short-stories/waiting_stars_de_bodard.mobi,,2918731,,39838379,,,,2013,17
"""  # noqa: E501
