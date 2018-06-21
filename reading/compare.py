# vim: ts=4 : sw=4 : et

import pandas as pd
import sys
from jinja2 import Template


ignore_columns = [
    'AvgRating',
]

################################################################################

# work out what books have been added, removed, had their edition changed, or
# have updates.
def compare(old, new):
    (old, new) = [df.fillna('') for df in (old, new)]

    # changed
    for ix in old.index.intersection(new.index):
        changed = _changed(old.loc[ix], new.loc[ix])
        if changed:
            print(changed)

    # added/removed/changed edition
    idcs = old.index.symmetric_difference(new.index)
    wids = pd.concat([
        old.loc[old.index.intersection(idcs)],
        new.loc[new.index.intersection(idcs)],
    ])['Work'].drop_duplicates().values

    for ix in wids:
        _o = old[old['Work'] == ix]
        _n = new[new['Work'] == ix]

        if len(_o) and len(_n):
            changed = _changed(_o.iloc[0], _n.iloc[0])
            if changed:
                print(changed)
        elif len(_n):
            print(_added(_n.iloc[0]))
        else:
            print(_removed(_o.iloc[0]))


################################################################################

# formatting for a book that's been added/removed/changed
def _added(book):
    return Template('''Added {{b.Title}} by {{b.Author}} to shelf '{{b.Shelf}}'
{%- if b.Series %}
  * {{b.Series}} series{% if b.Entry %}, Book {{b.Entry|int}}{%endif %}
{%- endif %}
  * {% if b.Category %}{{b.Category}}{% else %}Category not found{% endif %}
  * {{b.Pages|int}} pages
  * Language: {{b.Language}}
''').render(b=book)


def _removed(book):
    return Template('''Removed {{b.Title}} by {{b.Author}} from shelf '{{b.Shelf}}'
''').render(b=book)


def _changed(old, new):
    columns = [c for c in new.index if c not in ignore_columns]

    old = old[columns]
    new = new[columns]

    if old.equals(new):
        # nothing changed
        return
    elif new['Shelf'] == 'currently-reading' != old['Shelf']:
        # started reading
        return _started(new)
    elif new['Shelf'] == 'read' != old['Shelf']:
        # finished reading
        return _finished(new)
    else:
        # just generally changed fields
		# FIXME really need a more elegant way of arranging the columns :-/
        return Template('''{{new.Author}}, {{new.Title}}
{%- for col in ( 'Author', 'Title', 'Shelf', 'Category', 'Series', 'Entry', 'Language', 'Pages', 'Scheduled', 'Added', 'Started', 'Read', 'Author Id', 'Series Id', 'Binding', 'Published', 'Work', 'Rating', 'AvgRating', 'Borrowed') -%}
  {%- if old[col] != new[col] %}

      {%- if old[col] and not new[col] %}
  * {{col}} unset (previously {{old[col]}})

      {%- elif new[col] and not old[col] %}
  * {{col}} set to {{new[col]}}

      {%- else %}
        {%- if col in ('Added', 'Started', 'Read') %}
  * {{col}}: {{old[col].date()}} → {{new[col].date()}}

        {%- elif col in ('Title', 'Author') %}
  * {{col}} changed from '{{old[col]}}'

        {%- elif new[col] is number %}
  * {{col}}: {{old[col]|int}} → {{new[col]|int}}

        {%- else %}
  * {{col}}: {{old[col]}} → {{new[col]}}

        {%- endif %}
      {%- endif %}
  {%- endif -%}
{%- endfor %}
''').render(old=old, new=new)


################################################################################

def _started(book):
    return Template('''Started {{ b.Title }} by {{b.Author}}
  * {{b.Pages|int}} pages
''').render(b=book)


def _finished(book):
    return Template('''Finished {{b.Title}} by {{b.Author}}
  {{b.Started.date()}} → {{b.Read.date()}} ({{(b.Read - b.Started).days}} days)
  {{b.Pages|int}} pages, {{(b.Pages / (b.Read - b.Started).days)|round|int}} pages/day
  Rating: {{b.Rating|int}}
''').render(b=book)


################################################################################

if __name__ == "__main__":
    from .collection import Collection
    old = Collection(gr_csv=sys.argv[1]).df.fillna('')
    new = Collection(gr_csv=sys.argv[2]).df.fillna('')

    _changed(old, new)

