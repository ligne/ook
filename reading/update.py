# vim: ts=4 : sw=4 : et

"""The update command."""

import pandas as pd

from .collection import Collection, _process_fixes, expand_ebooks
from .compare import compare
from .goodreads import get_books
from .scrape import rebuild, scrape
from .storage import load_df, save_df
from .wordcounts import process


def update_goodreads(args, old, config):
    new = get_books(
        user_id=config("goodreads.user"),
        api_key=config("goodreads.key"),
        start_date=config("goodreads.start"),
    )

    if not args.ignore_changes:
        save_df("goodreads", new)

    compare(old, new)

    # FIXME update series

    return new


def update_kindle(args, old, config):
    new = process(old, config("kindle.directory"), force=args.force)

    if not args.ignore_changes:
        save_df("ebooks", new)

    compare(old, new, use_work=False)

    return new


def update_scrape(args, old, config):
    old = Collection.from_dir().df

    c = Collection.from_dir(fixes=None)
    df = c.df

    fixes = rebuild(scrape(config("goodreads.html")), df)

    if not args.ignore_changes:
        save_df("scraped", fixes)

    new = Collection.from_dir().df

    compare(old, new)

    return new


################################################################################


def main(args, config):
    old = Collection.from_dir().df

    goodreads = load_df("goodreads")
    ebooks = load_df("ebooks")
    scraped = load_df("scraped")
    books = load_df("books")
    authors = load_df("authors")

    # update the base layers
    if args.goodreads:
        goodreads = update_goodreads(args, goodreads, config)
    if args.kindle:
        ebooks = update_kindle(args, ebooks, config)

    # assign/derive the additional ebook columns
    ebooks = expand_ebooks(ebooks, config("kindle.words_per_page"))

    # update the overlays
    if args.scrape:
        scraped = update_scrape(args, scraped, config)

    # assemble the basic collection
    new = pd.concat([goodreads, ebooks], sort=False)

    # apply the various layers of fixes
    new.update(scraped)
    # FIXME
    new.update(load_df("metadata", fname="data/metadata-ebooks.csv"))
    new.update(load_df("metadata", fname="data/metadata-gr.csv"))
    new.update(_process_fixes(config("fixes")))

    compare(old, new)

    # save if necessary
    if args.save:
        save_df("goodreads", goodreads, fname="shadow/goodreads.csv")
        save_df("ebooks", ebooks, fname="shadow/ebooks.csv")
        save_df("scraped", scraped, fname="shadow/scraped.csv")
        save_df("books", books, fname="shadow/books.csv")
        save_df("authors", authors, fname="shadow/authors.csv")
