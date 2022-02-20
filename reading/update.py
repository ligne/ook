# vim: ts=4 : sw=4 : et

"""The update command."""

from .collection import Collection
from .compare import compare
from .config import config
from .goodreads import get_books
from .scrape import rebuild, scrape
from .storage import load_df, save_df
from .wordcounts import process


def update_goodreads(args, old):
    new = get_books()

    if not args.ignore_changes:
        save_df("goodreads", new)

    compare(old, new)

    # FIXME update series


def update_kindle(args, old):
    new = process(old, force=args.force)

    if not args.ignore_changes:
        save_df("ebooks", new)

    compare(old, new, use_work=False)


def update_scrape(args, old):
    c = Collection.from_dir(fixes=None)
    df = c.df

    fixes = rebuild(scrape(config('goodreads.html')), df)

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
    if "goodreads" in args.update:
        update_goodreads(args, goodreads)
    if "kindle" in args.update:
        update_kindle(args, ebooks)
    if "scrape" in args.update:
        update_scrape(args, scraped)
