# vim: ts=4 : sw=4 : et

"""Code for gathering ebooks, their metadata and length."""

from pathlib import Path
from subprocess import CalledProcessError, run
import sys
from tempfile import NamedTemporaryFile

import attr
import pandas as pd


# return a file (which may be the original) containing the contents of $path
# as text
def _as_text(path):
    if path.suffix == ".txt":
        return path.read_bytes()

    cmd = "pdftotext" if path.suffix == ".pdf" else "ebook-convert"

    tmpfile = NamedTemporaryFile(suffix=".txt")

    try:
        run([cmd, str(path), tmpfile.name], capture_output=True, check=True)
    except OSError:
        # ebook-convert probably doesn't exist
        return None
    except CalledProcessError as e:
        # it fell over
        print(e)
        return None

    return tmpfile.read()


# counts the words in $textfile. FIXME trim standard headers/footers?
def _count_words(textfile):
    return len(textfile.split()) if textfile is not None else None


# gathers metadata from the ebook.  annoyingly, calibre doesn't support
# Python3, and there aren't many other easy options...
def _read_metadata(path) -> dict[str, str]:
    sys.path.insert(0, "/usr/lib/calibre")
    sys.resources_location = "/usr/share/calibre"  # type: ignore[attr-defined]
    sys.extensions_location = "/usr/lib/calibre/calibre/plugins"  # type: ignore[attr-defined]

    from calibre.ebooks.metadata.meta import get_metadata

    ext = path.suffix[1:]
    ext = ext if ext in ["txt", "pdf"] else "mobi"
    mi = get_metadata(open(path, "r+b"), ext, force_read_metadata=True)
    return {
        "Title": mi.get("title"),
        "Authors": mi.get("authors"),
        "Languages": mi.get("languages"),
    }


@attr.s
class Metadata:
    metadata = attr.ib()

    @property
    def author(self):
        """Return the Author of the ebook."""
        author = self.metadata["Authors"][0]
        return "" if author == "Unknown" else author

    @property
    def title(self):
        """Return the Title of the ebook."""
        return self.metadata["Title"]

    @property
    def language(self):
        """Return the Language of the ebook, defaulting to "en" if missing."""
        try:
            return self.metadata["Languages"][0][:2]
        except (KeyError, IndexError):
            return "en"


def _ignore_item(path):
    ignore_fname = ["My Clippings.txt"]
    ignore_ext = [".kfx"]

    return (
        not path.is_file()
        or path.name[0] == "."
        or path.name in ignore_fname
        or path.suffix in ignore_ext
    )


def get_ebooks(kindle_dir):
    """Find all the interesting-looking files in $kindle_dir."""
    for d in "articles", "short-stories", "books", "non-fiction":
        category = "novels" if d == "books" else d
        for f in (kindle_dir / d).iterdir():
            if _ignore_item(f):
                continue
            yield (category, f, str(Path(category, f.name)))

    for f in kindle_dir.iterdir():
        if _ignore_item(f):
            continue
        yield ("articles", f, str(Path("articles", f.name)))


def process(df, kindle_dir, force=False):
    kindle_dir = Path(kindle_dir)

    ebooks = []

    for category, path, name in get_ebooks(kindle_dir):
        if not force and name in df.index:
            ebook = df.loc[name].to_dict()
            ebook["BookId"] = name
            ebooks.append(ebook)
            continue

        # get the metadata and wordcount
        metadata = Metadata(_read_metadata(path))
        words = _count_words(_as_text(path))

        ebooks.append(
            {
                "BookId": name,
                "Author": metadata.author,
                "Title": metadata.title,
                "Category": category,
                "Language": metadata.language,
                "Added": pd.Timestamp(path.stat().st_mtime, unit="s").floor("D"),
                "Words": words,
            }
        )

    return pd.DataFrame(ebooks).set_index("BookId")
