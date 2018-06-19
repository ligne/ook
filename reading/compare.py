# vim: ts=4 : sw=4 : et

import pandas as pd
import sys

ignore_columns = [
    'AvgRating',
]

################################################################################

# work out what books have been added, removed, had their edition changed, or
# have updates.
def compare(old, new):
    (old, new) = [ df.fillna('') for df in (old, new) ]

    # changed
    for ix in old.index.intersection(new.index):
        _changed(old.loc[ix], new.loc[ix])

    # added/removed/changed edition
    idcs = old.index.symmetric_difference(new.index)
    wids = pd.concat([
        old.loc[old.index.intersection(idcs)],
        new.loc[new.index.intersection(idcs)],
    ])['Work'].drop_duplicates().values

    for ix in wids:
        _o = old[old['Work'] == ix]
        _n = new[new['Work'] == ix]

        if len(_o) and len(_n):
            _changed(_o.iloc[0], _n.iloc[0])
        elif len(_n):
            print(_added(_n.iloc[0]))
        else:
            print(_removed(_o.iloc[0]))


################################################################################

# formatting for a book that's been added/removed/changed
def _added(book):
    return "Added '{Title}' by {Author}\n  {Category}\n".format(**book)
    # FIXME print more information


def _removed(book):
    return "Removed '{Title}' by {Author}\n".format(**book)


def _changed(old, new):
    columns = [ c for c in new.index if c not in ignore_columns ]

    old = old[columns]
    new = new[columns]

    if old.equals(new):
        # nothing changed
        return
    elif new['Shelf'] == 'currently-reading' != old['Shelf']:
        # started reading
        print(_started(new))
    elif new['Shelf'] == 'read' != old['Shelf']:
        # finished reading
        print(_finished(new))
    else:
        # just generally changed fields
        print('{Author}, {Title}'.format(**new))
        for (col, v) in new.iteritems():
            if v == old[col]:
                continue

            # FIXME work out what the dtype is, and if one or the other value is
            # null, and handle accordingly.
            if not old[col]:
                print('  {} set to {}'.format(col, v))
            elif not v:
                print('  {} unset (previously {})'.format(col, old[col]))
            else:
                print('  {}: {} -> {}'.format(col, old[col], v))

    print()

    return ''


################################################################################

def _started(book):
    return """Started '{Title}' by {Author}
""".format(**book)


def _finished(book):
    book = book.copy()
    book['Time'] = (book.Read - book.Started).days
    book['PPD'] = book['Pages'] / book['Time']
    return """Finished '{Title}' by {Author}
  {Started} → {Read} ({Time} days)
  {Pages:0.0f} pages, {PPD:0.0f} pages/day
  Rating: {Rating}
""".format(**book)


################################################################################

if __name__ == "__main__":
    from .collection import Collection
    old = Collection(gr_csv=sys.argv[1]).df.fillna('')
    new = Collection(gr_csv=sys.argv[2]).df.fillna('')

    _changed(old, new)

