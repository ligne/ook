# vim: ts=4 : sw=4 : et

"""Code for updating the collection in various ways."""

import pandas as pd

from .collection import Collection, _process_fixes, expand_ebooks, rebuild_metadata
from .compare import compare
from .goodreads import get_books, update_books
from .scrape import scrape
from .storage import Store
from .wikidata import fetch_entities
from .wordcounts import process


# FIXME improve this signature?
def main(args, config):
    """Update the store from various sources, and optionally save."""
    store = Store()

    if args.goodreads:
        store.goodreads = get_books(
            user_id=config("goodreads.user"),
            api_key=config("goodreads.key"),
            start_date=config("goodreads.start"),
            ignore_series=config("series.ignore"),
        )
        # FIXME update series

    if args.kindle:
        store.ebooks = process(
            store.ebooks,
            config("kindle.directory"),
            force=args.force,
        )

    if args.scrape:
        store.scraped = scrape(
            config("goodreads.html"),
            store.scraped,
            store.goodreads,
        )

    if args.metadata:
        store.books = update_books(
            store.books,
            store.ebooks,
            api_key=config("goodreads.key"),
            ignore_series=config("series.ignore"),
        )
        authors = store.authors
        authors.update(pd.DataFrame(fetch_entities(authors.QID)).set_index("AuthorId"))
        store.authors = authors

    # rebuild the metadata now the updates are complete. goodreads and ebooks
    # have to be done separately, because pandas does not like indexes
    # containing multiple types
    #
    # first merge in the author fixes
    # FIXME it would be nice if these could fix goodread author data, but
    # without imposing the wikidata names (which don't play well with pen
    # names, etc.)
    fixes = pd.DataFrame(config("authors")).set_index("AuthorId")
    authors = store.authors.reindex(store.authors.index | fixes.index)
    authors.update(fixes)
    # now actually rebuild each piece
    store.ebook_metadata = rebuild_metadata(
        store.ebooks,
        store.books,
        authors,
    )
    store.gr_metadata = rebuild_metadata(
        store.goodreads,
        store.books,
        authors,
    )

    compare(
        old=Collection.from_dir().df,
        new=Collection.assemble(
            bases=[
                store.goodreads,
                expand_ebooks(store.ebooks, config("kindle.words_per_page")),
            ],
            overlays=[
                store.scraped,
                store.ebook_metadata,
                store.gr_metadata,
                _process_fixes(config("fixes")),
            ],
        ).df,
    )

    if args.save:
        store.save("shadow")
