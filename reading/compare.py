# vim: ts=4 : sw=4 : et

"""Code for reporting the changes between two Collections or dataframes."""

from jinja2 import Template
import pandas as pd

from reading.collection import Collection


ignore_columns = [
    "AvgRating",
]


################################################################################


# work out what books have been added, removed, had their edition changed, or
# have updates.
def compare(old: Collection, new: Collection) -> None:
    """Show how $old and $new dataframes differ, in a way that makes sense for ook."""

    _compare_with_work(
        old.all.fillna(""),
        new.all.fillna(""),
    )


def _compare_with_work(old, new):
    # changed
    for ix in old.index.intersection(new.index):
        changed = _changed(old.loc[ix], new.loc[ix])
        if changed:
            print(changed)

    # added/removed/changed edition
    idcs = old.index.symmetric_difference(new.index)
    wids = (
        pd.concat(
            [
                old.loc[old.index.intersection(idcs)],
                new.loc[new.index.intersection(idcs)],
            ],
            sort=False,
        )["Work"]
        .drop_duplicates()
        .values
    )

    for ix in wids:
        _o = old[old["Work"] == ix]
        _n = new[new["Work"] == ix]

        if not _o.empty and not _n.empty:
            changed = _changed(_o.iloc[0], _n.iloc[0])
            if changed:
                print(changed)
        elif not _n.empty:
            print(_added(_n.iloc[0]))
        else:
            print(_removed(_o.iloc[0]))


################################################################################


# formatting for a book that's been added/removed/changed
def _added(book):
    return Template(
        """Added {{b.Title}} by {{b.Author}} to shelf '{{b.Shelf}}'
{%- if b.Series %}
  * {{b.Series}} series{% if b.Entry %}, Book {{b.Entry|int}}{%endif %}
{%- endif %}
  * {% if b.Category %}{{b.Category}}{% else %}Category not found{% endif %}
  * {% if "Pages" in b %}{{b.Pages|int}} pages{% else %}{{b.Words|int}} words{% endif %}
  * Language: {{b.Language}}
"""
    ).render(b=book)


def _removed(book):
    return Template(
        """Removed {{b.Title}} by {{b.Author}} from shelf '{{b.Shelf}}'
"""
    ).render(b=book)


def _changed(old, new):
    columns = [c for c in new.index if c not in ignore_columns]

    old = old[columns]
    new = new[columns]

    if old.equals(new):
        # nothing changed
        return None
    elif new["Shelf"] == "currently-reading" != old["Shelf"]:
        # started reading
        return _started(new)
    elif new["Shelf"] == "read" != old["Shelf"]:
        # finished reading
        return _finished(new)
    else:
        # just generally changed fields
        return Template(
            """{{new.Author}}, {{new.Title}}
{%- for col in new.index -%}
  {%- if old[col] != new[col] %}

      {%- if old[col] and not new[col] %}
        {%- if col in ('Scheduled') %}
  * Unscheduled for {{old[col].year}}
        {%- else %}
  * {{col}} unset (previously {{old[col]}})
        {%- endif %}

      {%- elif new[col] and not old[col] %}
        {%- if col in ('Scheduled') %}
  * {{col}} for {{new[col].year}}
        {%- elif new[col] is number %}
  * {{col}} set to {{new[col]|int}}
        {%- else %}
  * {{col}} set to {{new[col]}}
        {%- endif %}

      {%- else %}
        {%- if col in ('Added', 'Started', 'Read') %}
  * {{col}}: {{old[col].date()}} → {{new[col].date()}}

        {%- elif col in ('Title', 'Author') %}
  * {{col}} changed from '{{old[col]}}'

        {%- elif col in ('Scheduled') %}
  * {{col}}: {{old[col].year}} → {{new[col].year}}

        {%- elif new[col] is number %}
  * {{col}}: {{old[col]|int}} → {{new[col]|int}}

        {%- else %}
  * {{col}}: {{old[col]}} → {{new[col]}}

        {%- endif %}
      {%- endif %}
  {%- endif -%}
{%- endfor %}
"""
        ).render(old=old, new=new)


################################################################################


def _started(book):
    return Template(
        """Started {{ b.Title }} by {{b.Author}}
{%- if b.Series and b.Series is not number %}
  * {{b.Series}} series{% if b.Entry %}, Book {{b.Entry|int}}{%endif %}
{%- endif %}
  * {% if b.Category %}{{b.Category}}{% else %}Category not found{% endif %}
  * {{b.Pages|int}} pages
  * Language: {{b.Language}}
"""
    ).render(b=book)


# FIXME display more information (including category and author
# gender/nationality) for checking
def _finished(book):
    return Template(
        """Finished {{b.Title}} by {{b.Author}}
  * {{b.Started.date()}} → {{b.Read.date()}} ({{(b.Read - b.Started).days}} days)
  {%- if b.Pages|int %}
  * {{b.Pages|int}} pages, {{(b.Pages / ((b.Read - b.Started).days + 1))|round|int}} pages/day
  {%- endif %}
  * Rating: {{b.Rating|int}}
  * Category: {{b.Category}}
  * Published: {{b.Published|int}}
  * Language: {{b.Language}}
"""
    ).render(b=book)


################################################################################


if __name__ == "__main__":
    import argparse

    from reading.config import Config
    from reading.storage import Store, load_df

    parser = argparse.ArgumentParser()
    parser.add_argument("--goodreads")
    parser.add_argument("--ebooks")

    args = parser.parse_args()

    store = Store()
    if args.goodreads:
        store.goodreads = load_df("goodreads", args.goodreads)
    if args.ebooks:
        store.ebooks = load_df("ebooks", args.ebooks)

    config = Config.from_file()

    compare(
        old=Collection.from_store(store, config),
        new=Collection.from_dir(),
    )
