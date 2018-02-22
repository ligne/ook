# vim: ts=4 : sw=4 : et

import pandas as pd
import sys

columns = [
    'Title',
    'Author',
    'Date Added',
    'Date Started',
    'Date Read',
    'Bookshelves',
    'Exclusive Shelf',
    'My Rating',
    'Binding',
    'Number of Pages',
]


def compare(old, new):
    s = ''

    # changed
    for ix in old.index.intersection(new.index):
        orow = old.ix[ix][columns].fillna('')
        nrow = new.ix[ix][columns].fillna('')

        if nrow.equals(orow):
            continue

        # special cases:
        #   finished reading a book

        s += '{Author}, {Title}\n'.format(**nrow)
        for (col, v) in nrow.iteritems():
            if v == orow[col]:
                continue

            if col == 'Bookshelves':
                pass
#                old = set(old_row[col].split(', '))
#                new = set(new_row[col].split(', '))
#
#                added   = new - old - set([new_row['Exclusive Shelf']])
#                removed = old - new - set([old_row['Exclusive Shelf']])
#
#                if not (added or removed):
#                    continue
#
#                print '{}:'.format(col)
#                if removed:
#                    print '  -{}'.format(', -'.join(removed)),
#                if added:
#                    print '  +{}'.format(', +'.join(added)),
#                print
            else:
                s += '{}:\n  {} -> {}\n'.format(col, orow[col], v)

        s += '---\n\n'

#    g = pd.concat([
#        new.ix[new.index.difference(old.index)],
#        old.ix[old.index.difference(new.index)],
#    ]).groupby('Work Id')
#
#    for work, group in g:
#        if len(group) == 2:
#            # it's changed
#            print(group)
#        elif len(group) == 1:
#            # it's added/removed
#            pass
#        else:
#            print('wtf? group size {} for work {}'.format(len(group), work))
#
#    return ''


    # FIXME handle edition changes
    for ix in new.index.difference(old.index):
        row = new.ix[ix]

        fmt = "Added '{Title}' by {Author}\n"
#        if row['Series']:
#            fmt += ' ({Series}, book {Entry})'
        s += fmt.format(**row)
        # also show any bookshelves it's been added to
        s += '  Bookshelves: {Bookshelves}\n'.format(**row)
        s += '---\n\n'

    # removed
    for ix in old.index.difference(new.index):
        row = old.ix[ix]
        s += "Removed '{Title}' by {Author}\n".format(**row)
        s += '  Bookshelves: {Bookshelves}\n'.format(**row)
        s += '---\n\n'

    return s


if __name__ == "__main__":
    import pandas as pd
    old = pd.read_csv(sys.argv[1], index_col=0)
    new = pd.read_csv(sys.argv[2], index_col=0)

    print(compare(old, new))

