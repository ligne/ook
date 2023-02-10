# vim: ts=4 : sw=4 : et

import shutil

from jinja2 import Template
import pandas as pd

from .collection import Collection, _ebook_parse_title, rebuild_metadata
from .compare import compare
from .config import Config
from .goodreads import fetch_book, search_title
from .storage import Store, load_df, save_df
from .wikidata import entity, wd_search


################################################################################


class SaveExit(Exception):
    """Save and exit."""


class FullExit(Exception):
    """Exit without saving."""


################################################################################


# formats a list of book search results
def _list_book_choices(results, author_ids, work_ids):
    (width, _) = shutil.get_terminal_size()
    return Template(
        """
{%- for entry in results %}
  {%- if loop.first %}\033[1m{% endif %} {{loop.index}}. {%- if loop.first %}\033[0m{% endif %}
  {%- if entry.Work|int in works %}\033[32m{% endif %} {{entry.Title|truncate(width-5)}}\033[0m
    {%- if entry.Author %}
      {%- if entry.AuthorId|int in authors %}\033[33m{% endif %}
      {{entry.Author}}\033[0m
    {%- endif %}
    {%- if entry.Description %}
      {{entry.Description}}
    {%- endif %}
    {%- if entry.Published %}
      Published: {{entry.Published}}
    {%- endif %}
    {%- if entry.Ratings %}
      Ratings: {{entry.Ratings}}
    {%- endif %}
    {%- if entry.BookId %}
      https://www.goodreads.com/book/show/{{entry.BookId}}
    {%- endif %}
    {%- if entry.AuthorId %}
      https://www.goodreads.com/author/show/{{entry.AuthorId}}
    {%- endif %}
{% endfor %}
"""
    ).render(results=results, authors=author_ids, works=work_ids, width=width)


# formats a list of author search results
def _list_author_choices(results):
    (width, _) = shutil.get_terminal_size()
    return Template(
        """
{%- for entry in results %}
  {%- if loop.first %}\033[1m{% endif %} {{loop.index}}. {%- if loop.first %}\033[0m{% endif %}
 {%- if True %} {{entry.Label}}{% endif %}
    {%- if entry.Description %}
    {{entry.Description}}
    {%- endif %}
{% endfor %}
"""
    ).render(results=results, width=width)


# prompts the user for a selection or other decision.
def _read_choice(n):
    entries = [str(x + 1) for x in range(n)]
    others = list("sqQ")

    selections = "1" if n == 1 else "1-{}".format(n)

    prompt = "\033[94m[{},?]?\033[0m ".format(",".join([selections] + others))

    help_msg = (
        "\033[91m"
        + """
{} - select

s - skip to the next author
q - save and exit
Q - exit without saving
? - print help
""".format(
            selections
        ).strip()
        + "\033[0m"
    )

    try:
        while True:
            c = input(prompt) or "1"
            if c == "q":
                raise SaveExit
            elif c == "Q":
                raise FullExit
            elif c == "s":
                return None
            elif c in entries:
                break
            print(help_msg)
    except EOFError:
        # Ctrl-D
        print()
        raise SaveExit  # pylint: disable=raise-missing-from
    except KeyboardInterrupt:
        print()
        raise FullExit  # pylint: disable=raise-missing-from

    return c


################################################################################


def lookup_work_id(book, author_ids, work_ids, config):
    print("\033[1mSearching for '{}' by '{}'\033[0m".format(book.Title, book.Author))

    title = _ebook_parse_title(book.Title).Title
    results = sorted(search_title(title, config("goodreads.key")), key=lambda x: -x["Ratings"])
    if not results:
        # halp!
        print("No books found with the title '{}'".format(title))
        print()
        return None

    # page these?
    if len(results) > 10:
        results = results[:10]

    print(_list_book_choices(results, author_ids, work_ids))
    response = _read_choice(len(results))

    return results[int(response) - 1] if response else None


# associates an AuthorId with a Wikidata QID
def lookup_author(author):
    (width, _) = shutil.get_terminal_size()
    print(
        Template(
            """
\033[1mSearching for '{{author}}'\033[0m
{{titles|join(', ')|truncate(width)}}\033[0m
""".lstrip()
        ).render(author=author.Author, titles=author.Title, width=width)
    )

    results = wd_search(author.Author)
    if not results:
        print("Unable to find '{}' in Wikidata".format(author.Author))
        print()
        # TODO search harder
        return None

    print(_list_author_choices(results))
    response = _read_choice(len(results))

    return results[int(response) - 1] if response else None


# check the author data looks reasonable
# FIXME Do This Properly, and allow editing
def confirm_author(e):
    """Get user confirmation and return a dict of the interesting fields."""
    print(f"\n\033[32m{e.label}: {e.gender}, {e.nationality}\033[0m")
    c = input("Is this correct? [Y/n] ")
    print()

    return (
        None
        if (c and c != "y")
        else {
            "QID": e.qid,
            "Author": e.label,
            "Gender": e.gender,
            "Nationality": e.nationality,
            "Description": e.description,
        }
    )


################################################################################


def find(what, config):
    books = load_df("books")
    authors = load_df("authors")

    try:
        if "books" in what:
            find_books(books, config)
        # FIXME want to reload so the authors of newly-associated books appear
        if "authors" in what:
            find_authors(authors)
    except SaveExit:
        pass
    except FullExit:
        return

    save_df("books", books)
    save_df("authors", authors)


# associate WorkIds with book IDs
def find_books(books, config):
    df = Collection.from_dir().categories("articles", exclude=True).df  # include metadata

    author_ids = set(df.AuthorId.dropna().astype(int))
    work_ids = set(df.Work.dropna().astype(int))

    df = df[df.Work.isnull()]
    df = df[df.Language == "en"]  # search doesn't work well with non-english books

    for book_id, book in df.sample(frac=1).iterrows():
        resp = lookup_work_id(book, author_ids, work_ids, config)
        if not resp:
            continue

        author_ids.add(resp["AuthorId"])
        work_ids.add(resp["Work"])

        books.loc[book_id] = pd.Series(
            fetch_book(
                resp["BookId"],
                config("goodreads.key"),
                config("series.ignore"),
            )
        )
        books.loc[book_id, "Work"] = resp["Work"]
        books.loc[book_id, "BookId"] = resp["BookId"]


# associate Wikidata QIDs with AuthorIds
def find_authors(authors):
    df = Collection.from_dir().df
    df = (
        df[~df.AuthorId.isin(authors.index)]
        .groupby("AuthorId")
        .aggregate(
            {
                "Author": "first",
                "Title": list,
            }
        )
    )

    for author_id, author in df.iterrows():
        resp = lookup_author(author)
        if not resp:
            continue

        author = confirm_author(entity(resp["QID"]))
        if author:
            authors.loc[int(author_id)] = author


################################################################################


def main(args, config: Config) -> None:
    """Interactively search for metadata, and optionally save the results."""
    store = Store()

    # FIXME pass in the Store so find_authors can include those of the newly-found books
    # FIXME do this check in cmds.py
    if args.find:
        find(args.find, config)

    # merge in the author fixes
    fixes = pd.DataFrame(config("authors")).set_index("AuthorId")
    authors = store.authors
    authors = authors.reindex(authors.index | fixes.index)
    authors.update(fixes)
    # actually rebuild it
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
        new=Collection.from_store(store, config).df,
    )

    if args.save:
        store.save("shadow")
