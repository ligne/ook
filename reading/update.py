# vim: ts=4 : sw=4 : et

"""The update command."""

from .collection import Collection
from .compare import compare
from .config import config
from .goodreads import get_books
from .scrape import rebuild
from .scrape import scrape as _scrape
from .storage import load_df, save_df
from .wordcounts import process


def goodreads(args):
    old = load_df("goodreads")
    new = get_books()

    if not args.ignore_changes:
        save_df("goodreads", new)

    compare(old, new)

    # FIXME update series


def kindle(args):
    old = load_df("ebooks")
    new = process(old, force=args.force)

    if not args.ignore_changes:
        save_df("ebooks", new)

    compare(old, new, use_work=False)


def scrape(args):
    c = Collection.from_dir(fixes=None)
    df = c.df

    old = Collection.from_dir().df

    fixes = rebuild(_scrape(config('goodreads.html')), df)

    if not args.ignore_changes:
        save_df("scraped", fixes)

    new = Collection.from_dir().df

    compare(old, new)


################################################################################

def main(args):
    old = Collection.from_dir().df

    goodreads = load_df("goodreads")
    ebooks = load_df("ebooks")
    scraped = load_df("scraped")
    books = load_df("books")
    authors = load_df("authors")

    # dispatch to the update commands in a sensible order
    if 'goodreads' in args.update:
        goodreads(args)
    if 'kindle' in args.update:
        kindle(args)
    if 'scrape' in args.update:
        scrape(args)

