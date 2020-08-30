# vim: ts=4 : sw=4 : et

from reading.collection import Collection
from reading.storage import load_df, save_df


def test_load_df():
    df = load_df("authors")
    assert df is not None, "Loaded an existing dataframe"

    df = load_df("authors", fname="/does/not/exist")
    assert df.empty, "Loaded a dataframe from a missing file"


def test_save_df(tmp_path):
    df = Collection.from_dir("t/data/2019-12-04", fixes=False, metadata=False).df

    # pick out a few books
    df = df[df.AuthorId == 9121]

    sorted_csv = tmp_path / "ebooks.csv"
    save_df("ebooks", df, sorted_csv)
    assert sorted_csv.read_text() == """\
BookId,Author,Title,Category,Language,Words,Added
38290,James Fenimore Cooper,The Pioneers,novels,,,2017-02-27
246245,James Fenimore Cooper,The Deerslayer,novels,en,,2016-11-08
347245,James Fenimore Cooper,The Pathfinder,novels,en,,2016-11-08
621017,James Fenimore Cooper,The Prairie,novels,,,2016-11-08
1041744,James Fenimore Cooper,The Last of the Mohicans,novels,,,2017-02-16
""", "Wrote a csv of only some columns"

    shuffled_df = df[sorted(df.columns)].sample(frac=1)
    shuffled_csv = tmp_path / "shuffled.csv"
    save_df("ebooks", shuffled_df, shuffled_csv)
    assert shuffled_csv.read_text() == """\
BookId,Author,Title,Category,Language,Words,Added
38290,James Fenimore Cooper,The Pioneers,novels,,,2017-02-27
246245,James Fenimore Cooper,The Deerslayer,novels,en,,2016-11-08
347245,James Fenimore Cooper,The Pathfinder,novels,en,,2016-11-08
621017,James Fenimore Cooper,The Prairie,novels,,,2016-11-08
1041744,James Fenimore Cooper,The Last of the Mohicans,novels,,,2017-02-16
""", "CSV is ordered even if the df isn't"
