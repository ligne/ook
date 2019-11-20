# vim: ts=4 : sw=4 : et

import sys
import shutil
from jinja2 import Template
import pandas as pd

from .collection import Collection
from .wikidata import wd_search
from .wikidata import Entity
from .goodreads import search_title, fetch_book

from .collection import _ebook_parse_title


class SaveExit(Exception):
    pass

class FullExit(Exception):
    pass


# formats a list of book search results
def _list_book_choices(results, author_ids, work_ids):
    (width,_) = shutil.get_terminal_size()
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
    (width,_) = shutil.get_terminal_size()
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

    selections = n == 1 and '1' or '1-{}'.format(n)

    prompt = '\033[94m[{},?]?\033[0m '.format(','.join([selections] + others))

    help_msg = '\033[91m' +  '''
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
                return
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

def lookup_work_id(metadata, author_ids, work_ids):
    title = _ebook_parse_title(metadata.Title).Title
    results = sorted(search_title(title), key=lambda x: -x['Ratings'])
    if not results:
        # halp!
        print("No books found with the title '{}'".format(title))
        print()
        return

    # page these?
    if len(results) > 10:
        results = results[:10]

    print(_list_book_choices(results, author_ids, work_ids))
    response = _read_choice(len(results))

    if not response:
        return
    return results[int(response)-1]


# associates an AuthorId with a Wikidata QID
def lookup_author(author_id, author):
    (width,_) = shutil.get_terminal_size()
    print(Template('''
\033[1mSearching for '{{author}}'\033[0m
{{titles|join(', ')|truncate(width)}}\033[0m
'''.lstrip()).render(author=author.Author, titles=author.Title, width=width))

    results = wd_search(author.Author)
    if not results:
        print("Unable to find '{}' through wikidata search".format(name))
        # TODO search harder
        return

    print(_list_author_choices(results))
    response = _read_choice(len(results))

    if not response:
        return

    return results[int(response)-1]


# check the author data looks reasonable
# FIXME Do This Properly, and allow editing
def confirm_author(author):
    entity = Entity(author['QID'])

    author['Gender']      = entity.gender()
    author['Nationality'] = entity.nationality()

    print('\n\033[32m{Label}: {Gender}, {Nationality}\033[0m'.format(**author))
    c = input('Is this correct? [Y/n] ')
    print()

    return None if c == 'n' else author


################################################################################

# associate Wikidata QIDs with AuthorIds
def find_authors():
    df = Collection().df
    authors = pd.DataFrame()

    # FIXME need to filter out authors who have already been done
    g = df.groupby('AuthorId').aggregate({
        'Author': 'first',
        'Title': lambda x: list(x),
    })

    for (author_id, author) in g.iterrows():
        try:
            resp = lookup_author(author_id, author)
            if not resp:
                continue

            confirm_author(resp)
        except (SaveExit):
            break
        except (FullExit):
            sys.exit()


################################################################################

if __name__ == '__main__':
    print(lookup_author(sys.argv[1:]))

