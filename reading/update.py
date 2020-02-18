# vim: ts=4 : sw=4 : et

from .collection import Collection
from .compare import compare
from .config import config


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
        df.sort_index().to_csv("data/goodreads.csv", float_format="%.20g")

    compare(old.df, df)

    # FIXME update series


def kindle(args):
    from .wordcounts import process

    old = Collection(
        shelves=['kindle'],
        # FIXME Collection shouldn't ignore articles by default: let suggest do that.
        categories=['novels', 'short-stories', 'non-fiction', 'articles'],
        metadata=False,
    ).df
    new = process(old, force=args.force)

    if not args.ignore_changes:
        Collection(df=new).save()

    new = new.assign(Work=None, Shelf='kindle')

    compare(old, new, use_work=False)


def scrape(args):
    from .scrape import scrape as _scrape, rebuild

    c = Collection(fixes=None)
    df = c.df

    old = Collection().df

    fixes = rebuild(_scrape(config('goodreads.html')), df)

    if not args.ignore_changes:
        fixes.to_csv('data/scraped.csv', float_format='%.20g')

    new = Collection().df

    compare(old, new)


################################################################################

def main(args):
    # dispatch to the update commands in a sensible order
    if 'goodreads' in args.update:
        goodreads(args)
    if 'kindle' in args.update:
        kindle(args)
    if 'scrape' in args.update:
        scrape(args)

