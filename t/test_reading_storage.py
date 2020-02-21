# vim: ts=4 : sw=4 : et

from reading.storage import load_df


def test_load_df():
    df = load_df("authors")
    assert df is not None, "Loaded an existing dataframe"

    df = load_df("authors", fname="/does/not/exist")
    assert df.empty, "Loaded a dataframe from a missing file"
