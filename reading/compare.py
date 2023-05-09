# vim: ts=4 : sw=4 : et

"""Code for reporting the changes between two Collections or dataframes."""

from collections.abc import Mapping, Sequence
from enum import Enum
from string import Formatter
from typing import Any, Optional, Union

from attr import define
from jinja2 import Template
import pandas as pd
from typing_extensions import Self

from reading.collection import Collection


ignore_columns = [
    "AvgRating",
]

################################################################################


class ChangeDirection(Enum):
    """The direction of a field's change."""

    SET = "set"
    UNSET = "unset"
    CHANGED = "changed"
    UNCHANGED = "unchanged"
    MISSING = "missing"


@define
class ChangedField:
    """A single changed field."""

    name: str
    old: Any
    new: Any

    @property
    def direction(self) -> ChangeDirection:
        """Describe the type of field change that has occurred."""
        if pd.isna(self.old) and pd.isna(self.new):
            return ChangeDirection.MISSING
        if pd.isna(self.old):
            return ChangeDirection.SET
        if pd.isna(self.new):
            return ChangeDirection.UNSET
        if self.old != self.new:
            return ChangeDirection.CHANGED
        return ChangeDirection.UNCHANGED


################################################################################


class ChangeEvent(Enum):
    """The type of change."""

    STARTED = "started"
    FINISHED = "finished"
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    UNMODIFIED = "unmodified"


@define
class Change:
    """A change between two (hopefully equivalent) book entries."""

    old: Optional[pd.Series]
    new: Optional[pd.Series]

    def change(self, field: str) -> ChangedField:
        """Return an object representing the change of column $field."""
        return ChangedField(
            field,
            self.old[field] if self.old is not None else None,
            self.new[field] if self.new is not None else None,
        )

    @property
    def _change_mask(self) -> pd.Series:
        # which fields differ between old and new (which it assumes are both defined)
        return ~((self.old == self.new) | (self.old.isna() & self.new.isna()))

    @property
    def is_added(self) -> bool:
        """Indicate whether this book did not previously exist."""
        return self.old is None

    @property
    def is_removed(self) -> bool:
        """Indicate whether this book no longer exists."""
        return self.new is None

    @property
    def is_started(self) -> bool:
        """Indicate whether this book has just been started."""
        shelf = self.change("Shelf")
        return bool(shelf.old != shelf.new == "currently-reading")

    @property
    def is_finished(self) -> bool:
        """Indicate whether this book has just been finished."""
        shelf = self.change("Shelf")
        return bool(shelf.old != shelf.new == "read")

    @property
    def is_modified(self) -> bool:
        """Indicate whether fields in this book have been modified."""
        # FIXME or would this be useful if it were more generally true?
        return self.old is not None and self.new is not None and not self.old.equals(self.new)

    @property
    def event(self) -> ChangeEvent:
        """Return an enum indicating what sort of change is involved."""
        return (
            ChangeEvent.STARTED
            if self.is_started
            else ChangeEvent.FINISHED
            if self.is_finished
            else ChangeEvent.ADDED
            if self.is_added
            else ChangeEvent.REMOVED
            if self.is_removed
            else ChangeEvent.MODIFIED
            if self.is_modified
            else ChangeEvent.UNMODIFIED
        )

    def changes(self) -> list[ChangedField]:
        """Return a ChangedField for each change."""
        if self.is_modified:
            mask = self._change_mask
            return [self.change(field) for field in mask[mask].index]
        return []

    @property
    def book(self) -> pd.Series:
        """Return the most up-to-date version of this book."""
        assert (book := self.new if self.new is not None else self.old) is not None
        return book


################################################################################


@define
class FormattedValue:
    """A value that knows how to format itself."""

    value: Any
    default_format: str

    def __format__(self, format_spec: str, /) -> str:
        """Return a formatted version of $value, according to format_spec or using the default."""
        return format(self.value, format_spec or self.default_format)


@define
class ValueFormats:
    """Format specifications for individual values."""

    formats: Mapping[str, str] = {
        "datetime64[ns]": "%F",
        "float64": "0.0f",
    }

    def extend(self, changes: dict[str, str]) -> Self:
        """Amend the formats."""
        self.formats = self.formats | changes
        return self

    def find(self, *terms: str, default: str = "") -> str:
        """Return a suitable formatter string for the field, falling back on the dtype."""
        return next(
            (self.formats[t] for t in terms if t in self.formats),
            default,
        )


################################################################################


@define
class BookFormatter(Formatter):
    """Format books using format-strings."""

    dtypes: pd.Series
    value_formats: ValueFormats

    def format_value(self, field: str, value: Any) -> FormattedValue:
        """Return a value that will format correctly."""
        return FormattedValue(value, self.value_formats.find(field, str(self.dtypes[field])))

    def get_value(
        self,
        key: Union[int, str],
        args: Sequence[Any],
        kwargs: Mapping[str, FormattedValue],
    ) -> FormattedValue:
        """Convert a field name into the corresponding argument."""
        if isinstance(key, int):
            raise ValueError("Only string identifiers are supported.")

        # if it's not in kwargs, assume it's a column name
        return kwargs[key] if key in kwargs else self.format_value(key, args[0][key])


################################################################################


@define
class ChangeHeaderStyle(ValueFormats):
    """Format strings for header lines."""

    formats: Mapping[str, str] = {
        "started": "Started {Title} by {Author}",
        "finished": "Finished {Title} by {Author}",
        "added": "Added {Title} by {Author} to {Shelf}",
        "removed": "Removed {Title} by {Author} from {Shelf}",
        "modified": "{Author}, {Title}",
    }


@define
class BookStatementStyle(ValueFormats):
    """Format strings for statement lines."""

    formats: Mapping[str, str] = {
        "pages": "{Pages} pages",
        "category": "{Category}",
        "series": "{Series} series",
        "borrowed": "Borrowed is {Borrowed}",
    }


@define
class ChangeStyler:
    """Style a Change object."""

    formatter: BookFormatter

    # format strings
    header_style = ChangeHeaderStyle()
    statement_style = BookStatementStyle()

    def _header(self, change: Change) -> str:
        return self.formatter.format(self.header_style.find(change.event.value), change.book)

    def _statement(self, book: pd.Series, field: str) -> str:
        fmt = self.statement_style.find(field.lower(), default="{field}: {value}")
        value = self.formatter.format_value(field, book[field])

        return self.formatter.format(fmt, book, field=field, value=value)


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


def main() -> None:  # pragma: no cover
    """Command-line interface for debugging."""

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


if __name__ == "__main__":
    import argparse

    from reading.config import Config
    from reading.storage import Store, load_df

    main()
