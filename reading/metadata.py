# vim: ts=4 : sw=4 : et

import shutil

from jinja2 import Template
import pandas as pd

from .collection import Collection, _ebook_parse_title
from .compare import compare
from .config import config, df_columns, metadata_prefer
from .goodreads import fetch_book, search_title
from .storage import load_df, save_df
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
        raise SaveExit
    except KeyboardInterrupt:
        print()
        raise FullExit

    return c


################################################################################


def lookup_work_id(book, author_ids, work_ids):
    print("\033[1mSearching for '{}' by '{}'\033[0m".format(book.Title, book.Author))

    title = _ebook_parse_title(book.Title).Title
    results = sorted(search_title(title), key=lambda x: -x["Ratings"])
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


def find(what):
    books = load_df("books")
    authors = load_df("authors")

    try:
        if "books" in what:
            find_books(books)
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
def find_books(books):
    df = Collection.from_dir().categories(exclude=["articles"]).df  # include metadata

    author_ids = set(df.AuthorId.dropna().astype(int))
    work_ids = set(df.Work.dropna().astype(int))

    df = df[df.Work.isnull()]
    df = df[df.Language == "en"]  # search doesn't work well with non-english books

    for book_id, book in df.sample(frac=1).iterrows():
        resp = lookup_work_id(book, author_ids, work_ids)
        if not resp:
            continue

        author_ids.add(resp["AuthorId"])
        work_ids.add(resp["Work"])

        books.loc[book_id] = pd.Series(fetch_book(resp["BookId"]))
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


def rebuild(books, works, authors):
    """Rebuild the metadata and return it as a dataframe."""
    prefer_work_cols = metadata_prefer("work")
    prefer_book_cols = metadata_prefer("book")

    # add in any missing columns, to make things easier
    books = books.reindex(columns=df_columns("metadata"))

    # create an empty dataframe the right size
    metadata = pd.DataFrame().reindex_like(books)

    # fill in one set of columns
    metadata.update(books[prefer_work_cols])
    metadata.update(works[prefer_work_cols])

    # fill in the other
    metadata.update(works[prefer_book_cols])
    metadata.update(books[prefer_book_cols])

    # populate the author metadata
    metadata.update(
        metadata[metadata.AuthorId.isin(authors.index)].AuthorId.apply(
            lambda x: authors.loc[x, ["Gender", "Nationality"]]
        )
    )

    # filter out no-op changes and empty rows
    return metadata[books != metadata].dropna(how="all", axis="index")


################################################################################


def main(args):
    old = Collection.from_dir(fixes=False).df

    if args.find:
        find(args.find)

    # rebuild things
    books = load_df("books")

    # load the authors and add in the fixes
    authors = load_df("authors")
    fixes = pd.DataFrame(config("authors")).set_index("AuthorId")
    authors = authors.reindex(authors.index.union(fixes.index))
    authors.update(fixes)

    new = Collection.from_dir(metadata=False, fixes=False).df

    # this has to be done in two parts, because pandas does not like indexes
    # containing multiple types
    gr_metadata = rebuild(load_df("goodreads"), books, authors)
    ebook_metadata = rebuild(load_df("ebooks"), books, authors)

    new.update(gr_metadata)
    new.update(ebook_metadata)

    compare(old, new)

    if not args.ignore_changes:
        save_df("metadata", ebook_metadata, fname="data/metadata-ebooks.csv")
        save_df("metadata", gr_metadata, fname="data/metadata-gr.csv")
