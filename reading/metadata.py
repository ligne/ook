# vim: ts=4 : sw=4 : et

import shutil
from jinja2 import Template
import pandas as pd

from .collection import Collection
from .wikidata import wd_search
from .wikidata import Entity
from .goodreads import search_title, fetch_book

from .collection import _ebook_parse_title


################################################################################

class SaveExit(Exception):
    pass


class FullExit(Exception):
    pass


################################################################################

# formats a list of book search results
def _list_book_choices(results, author_ids, work_ids):
    (width, _) = shutil.get_terminal_size()
    return Template('''
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
''').render(results=results, authors=author_ids, works=work_ids, width=width)


# formats a list of author search results
def _list_author_choices(results):
    (width, _) = shutil.get_terminal_size()
    return Template('''
{%- for entry in results %}
  {%- if loop.first %}\033[1m{% endif %} {{loop.index}}. {%- if loop.first %}\033[0m{% endif %}
 {%- if True %} {{entry.Label}}{% endif %}
    {%- if entry.Description %}
    {{entry.Description}}
    {%- endif %}
{% endfor %}
''').render(results=results, width=width)


# prompts the user for a selection or other decision.
def _read_choice(n):
    entries = [str(x + 1) for x in range(n)]
    others = list('sqQ')

    selections = '1' if n == 1 else '1-{}'.format(n)

    prompt = '\033[94m[{},?]?\033[0m '.format(','.join([selections] + others))

    help_msg = '\033[91m' + '''
{} - select

s - skip to the next author
q - save and exit
Q - exit without saving
? - print help
'''.format(selections).strip() + '\033[0m'

    try:
        while True:
            c = input(prompt) or '1'
            if c == 'q':
                raise SaveExit
            elif c == 'Q':
                raise FullExit
            elif c == 's':
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
    results = sorted(search_title(title), key=lambda x: -x['Ratings'])
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
    print(Template('''
\033[1mSearching for '{{author}}'\033[0m
{{titles|join(', ')|truncate(width)}}\033[0m
'''.lstrip()).render(author=author.Author, titles=author.Title, width=width))

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
def confirm_author(author):
    entity = Entity(author['QID'])

    try:
        author['Gender']      = entity.gender()
        author['Nationality'] = entity.nationality()
    except Exception:  # FIXME
        print('\033[91mError fetching data\033[0m')
        print()
        return None

    print('\n\033[32m{Label}: {Gender}, {Nationality}\033[0m'.format(**author))
    c = input('Is this correct? [Y/n] ')
    print()

    return None if (c and c != 'y') else author


################################################################################

def _load_csv(name, columns):
    try:
        return pd.read_csv(name, index_col=0)
    except FileNotFoundError:
        return pd.DataFrame(columns=columns)


def find():
    books_csv   = 'data/books.csv'
    authors_csv = 'data/authors.csv'

    books = _load_csv(books_csv, [
        'Author',
        'AuthorId',
        'Published',
        'Title',
        'Pages',
        'Language',
        'Category',
        'Series',
        'SeriesId',
        'Entry',
    ])
    authors = _load_csv(authors_csv, [
        'QID',
        'Author',
        'Gender',
        'Nationality',
        'Description'
    ])

    try:
        find_books(books)
        # FIXME want to reload so the authors of newly-associated books appear
        find_authors(authors)
    except SaveExit:
        pass
    except FullExit:
        return

    books.to_csv(books_csv,     float_format='%.20g')
    authors.to_csv(authors_csv, float_format='%.20g')


# associate WorkIds with book IDs
def find_books(books):
    df = Collection().df  # include metadata

    author_ids = set(list(df.AuthorId.dropna().astype(int)))
    work_ids   = set(list(df.Work.dropna().astype(int)))

    df = df[df.Work.isnull()]
    df = df[df.Language == 'en']  # search doesn't work well with non-english books

    for (book_id, book) in df.sample(frac=1).iterrows():
        resp = lookup_work_id(book, author_ids, work_ids)
        if not resp:
            continue

        author_ids.add(resp['AuthorId'])
        work_ids.add(resp['Work'])

        books.loc[book_id] = pd.Series(fetch_book(resp['BookId']))
        books.loc[book_id, 'Work']   = resp['Work']
        books.loc[book_id, 'BookId'] = resp['BookId']


# associate Wikidata QIDs with AuthorIds
def find_authors(authors):
    df = Collection().df
    df = df[~df.AuthorId.isin(authors.index)].groupby('AuthorId').aggregate({
        'Author': 'first',
        'Title': list,
    })

    for (author_id, author) in df.iterrows():
        resp = lookup_author(author)
        if not resp:
            continue

        # FIXME save the QID?
        resp = confirm_author(resp)
        if not resp:
            continue

        resp['Author'] = resp.pop('Label')  # FIXME
        authors.loc[int(author_id)] = pd.Series(resp)


################################################################################

# regenerates the metadata based on what has been gathered.
def rebuild():
    books = Collection(metadata=False).df
    works = pd.read_csv('data/books.csv', index_col=0)

    prefer_work_cols = ['Work', 'Author', 'Title', 'Series', 'SeriesId', 'Entry', 'Published', 'Pages', 'AuthorId']
    prefer_book_cols = ['Language']

    books_mask = pd.concat([
        books.notnull()[prefer_book_cols],
        works.isnull()[prefer_work_cols],
    ], axis=1, sort=False)

    works_mask = pd.concat([
        works.notnull()[prefer_work_cols],
        books.isnull()[prefer_book_cols],
    ], axis=1, sort=False)

    metadata = pd.concat([
        works.where(works_mask),
        books.where(books_mask),
    ], sort=False)

    # filter out no-op changes and empty bits
    return metadata[books.loc[metadata.index, metadata.columns] != metadata] \
        .dropna(how='all') \
        .dropna(axis='columns', how='all')


################################################################################

if __name__ == '__main__':
    pass

