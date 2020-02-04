# vim: ts=4 : sw=4 : et

from .collection import Collection
from .compare import compare


def goodreads(args):
    from .goodreads import get_books

    df = get_books()

    # FIXME shortcut for this, please!
    old = Collection(shelves=[
        'read',
        'currently-reading',
        'pending',
        'elsewhere',
        'library',
        'ebooks',
        'to-read',
    ], fixes=False)

    if not args.ignore_changes:
        df.sort_index().to_csv('data/goodreads.csv', float_format='%g')

    compare(old.df, df)

    # FIXME update series


################################################################################

def main(args):
    # dispatch to the update commands in a sensible order
    if 'goodreads' in args.update:
        goodreads(args)

