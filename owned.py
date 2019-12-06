#!/usr/bin/python3

from jinja2 import Template

from reading.collection import Collection


def display(df):
    df = df[~df.Series.str.contains('Spirou', na=False)]
    df = df[~df.Author.str.contains('Georges Simenon')]

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


display(Collection(shelves=['pending', 'elsewhere', 'library'], merge=True).df)
display(Collection(shelves=['kindle'], merge=True).df)
display(Collection(shelves=['to-read'], merge=True).df)

df = Collection(shelves=['to-read', 'kindle', 'library'], merge=True).df
df = df[~df.Language.isnull() & (df.Language != 'en')]
display(df)

# vim: ts=4 : sw=4 : et
