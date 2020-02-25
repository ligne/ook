# vim: ts=4 : sw=4 : et

from .collection import Collection
from .compare import compare
from .config import config
from .storage import save_df


def goodreads(args):
    from .goodreads import get_books

    df = get_books()

    old = Collection(fixes=False).shelves(exclude=["kindle"])

    if not args.ignore_changes:
        save_df("goodreads", df)

    compare(old.df, df)

    # FIXME update series


def kindle(args):
    from .wordcounts import process

    old = Collection(metadata=False).shelves(['kindle']).df
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
        save_df("scraped", fixes)

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

