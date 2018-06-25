# vim: ts=4 : sw=4 : et

import sys
from jinja2 import Template

import reading.wikidata


# formats a list of search results
def _list_choices(results):
    return Template('''
{%- for entry in results %}
  {%- if loop.first %}\033[1m{% endif %} {{loop.index}}. {%- if loop.first %}\033[0m{% endif %} {{entry.Title}}
    {%- if entry.Author %}
      {{entry.Author}}
    {%- endif %}
    {%- if entry.Description %}
      {{entry.Description}}
    {%- endif %}
    {%- if entry.QID %}
      https://www.wikidata.org/wiki/{{entry.QID}}
    {%- elif entry.BookId %}
      https://www.goodreads.com/book/show/{{entry.BookId}}
    {%- endif %}
{% endfor %}
''').render(results=results)


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
  - load more information
  - load more results (?)
  - search harder
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

