# vim: ts=4 : sw=4 : et

import sys
import shutil
from jinja2 import Template

from .wikidata import wd_search
from .goodreads import search_title, fetch_book

import reading.collection


# formats a list of search results
def _list_choices(results, author_ids, work_ids):
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


# prompts the user for a selection or other decision.
def _read_choice(n):
    entries = [str(x) for x in range(1, n+1)]
    others = list('sqQ')

    selections = n == 1 and '1' or '1-{}'.format(n)

    opts = entries + others
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
            if c in opts:
                break
            print(help_msg)
    except EOFError:
        c = 'q'
        print()
    except KeyboardInterrupt:
        c = 'Q'
        print()

    return c


################################################################################

def lookup_work_id(metadata, author_ids, work_ids):
    title = reading.collection._ebook_parse_title(metadata.Title).Title
    results = sorted(search_title(title), key=lambda x: -x['Ratings'])
    if not results:
        # halp!
        print("No books found with the title '{}'".format(title))
        print()
        return 's'

    # page these?
    if len(results) > 10:
        results = results[:10]

    print(_list_choices(results, author_ids, work_ids))
    response = _read_choice(len(results))

    if response in 'sqQ':
        return response
    return results[int(response)-1]


def lookup_author(name, grid=None):
    results = reading.wikidata.search(name)
    if not results:
        print("Unable to find '{}' through wikidata search".format(name))
        # TODO search harder
        return

    print(_list_choices(results))
    response = _read_choice(len(results))

    if response in 'sqQ':
        return response
    else:
        #reading.wikidata.get_entity(qid)
        return results[int(response)-1]['QID']


################################################################################

if __name__ == '__main__':
    print(lookup_author(sys.argv[1:]))

