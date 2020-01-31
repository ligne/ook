# vim: ts=4 : sw=4 : et

from jinja2 import Template

from .collection import Collection
from .config import config

# report: a set of graphs going to a particular output
#   segment: a set of filters to apply to a Collection
#   filter: (column, pattern) filters to apply to all the segments in this report
#   output: the format to output


def _process_report(report):
    filters = report.get('filter', [])

    for segment in report['segments']:
        df = Collection(merge=True).df

        if 'shelves' in segment:
            df = df[df.Shelf.isin(segment['shelves'])]
        if 'languages' in segment:
            df = df[df.Language.isin(segment['languages'])]

        for col, pattern in filters:
            df = df[~df[col].str.contains(pattern, na=False)]

        yield df


def _display_report(df):
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


################################################################################

def main(args):
    for name in args.names:
        report = config('reports.' + name)
        df_list = _process_report(report)
        for df in df_list:
            _display_report(df)

