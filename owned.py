#!/usr/bin/python3

from jinja2 import Template

from reading.collection import Collection


def display(df):
    g = df.sort_values(['Author', 'Title']).groupby('Author')
    print(Template('''
{%- for author, books in groups %}
{{author}}
  {%- for book in books.itertuples() %}
* {{book.Title}}
  {%- endfor %}
{% endfor %}
----
''').render(groups=g))

display(Collection(shelves=['pending', 'elsewhere', 'library']).df)
display(Collection(shelves=['kindle']).df)
display(Collection(shelves=['to-read']).df)

# vim: ts=4 : sw=4 : et
