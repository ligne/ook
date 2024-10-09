# vim: ts=4 : sw=4 : et

"""Code for updating the collection in various ways."""

from __future__ import annotations

import pandas as pd

from .collection import Collection
from .compare import compare
from .config import Config
from .goodreads import get_books, update_books
from .scrape import scrape
from .storage import Store
from .wikidata import fetch_entities
from .wordcounts import process


# FIXME improve this signature?
def main(args, config: Config) -> None:
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

    compare(
        new=Collection.from_store(store, config),
        old=Collection.from_dir(),
    )

    if args.save:
        store.save("data")
    store.save("blah")
