# vim: ts=4 : sw=4 : et

from __future__ import annotations

from jinja2 import Template
import pandas as pd

from .collection import Collection
from .config import Config


# report: a set of graphs going to a particular output
#   segment: a set of filters to apply to a Collection
#   filter: (column, pattern) filters to apply to all the segments in this report
#   output: the format to output


def _process_report(report):
    filters = report.get("filter", [])

    for segment in report["segments"]:
        df = Collection.from_dir(merge=True).df

        if "shelves" in segment:
            df = df[df.Shelf.isin(segment["shelves"])]
        if "languages" in segment:
            df = df[df.Language.isin(segment["languages"])]

        for col, pattern in filters:
            df = df[~df[col].str.contains(pattern, na=False)]

        yield df


def flag(code):
    """Convert a string into the corresponding Unicode flag."""
    offset = ord("\N{REGIONAL INDICATOR SYMBOL LETTER A}") - ord("A")
    return chr(ord(code[0]) + offset) + chr(ord(code[1]) + offset)


# FIXME generalise this and put it somewhere more sensible
def prefix(book):
    """Return a prefix representing noteworthy properties of $book."""
    string = "".join(
        [
            ("\N{CIRCLED LATIN CAPITAL LETTER L}" if book.Shelf == "library" else ""),
            ("\N{CIRCLED LATIN CAPITAL LETTER S}" if book.Category == "short-stories" else ""),
            ("\N{CIRCLED LATIN CAPITAL LETTER N}" if book.Category == "non-fiction" else ""),
            (
                flag(book.Language.upper())
                if pd.notna(book.Language) and book.Language != "en"
                else ""
            ),
        ]
    )
    return f"{string} " if string else ""


def _display_report(df):
    g = df.sort_values(["Author", "Title"]).groupby("Author")

    print(
        Template(
            """
{%- for author, books in groups %}
{{author}}
  {%- for book in books.itertuples() %}
* {{prefix(book)}}{{book.Title}}
  {%- endfor %}
{% endfor %}
----
"""
        ).render(groups=g, prefix=prefix)
    )


################################################################################


def main(args, config: Config) -> None:
    for name in args.names:
        report = config("reports." + name)
        df_list = _process_report(report)
        for df in df_list:
            _display_report(df)
