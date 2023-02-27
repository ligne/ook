# vim: ts=4 : sw=4 : et

"""Functions for interfacing with WikiData."""

from __future__ import annotations

import json
import sys
from typing import Optional

import requests


# uppercases the first character of $s *only*
def _uc_first(text: str) -> str:
    return text[:1].upper() + text[1:]


def wd_search(term):
    """Search for $term using the basic WikiData search."""
    return _format_search_results(
        requests.get(
            "https://www.wikidata.org/w/api.php",
            params={
                "action": "wbsearchentities",
                "language": "en",
                "limit": 20,
                "format": "json",
                "search": term,
            },
        ).json()
    )


def _format_search_results(results) -> list[dict[str, str]]:
    return [
        {
            "Label": res["label"],
            "QID": res["id"],
            "Description": _uc_first(res.get("description", "")),
        }
        for res in results["search"]
    ]


###############################################################################


def entity(qid: str) -> Entity:
    """Return the Entity for $qid."""
    fname = "data/cache/wikidata/{}.json".format(qid)
    try:
        with open(fname) as fh:
            j = json.load(fh)
    except FileNotFoundError:
        url = f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"
        r = requests.get(url)
        with open(fname, "wb") as fh:
            fh.write(r.content)
        j = r.json()
    return Entity(j["entities"][qid])


class Entity:
    """Basic operations on a Wikidata entity."""

    # fetches an entity by its QID
    def __init__(self, e) -> None:
        self.entity = e

    @property
    def qid(self) -> str:
        """Return the QID for the entity."""
        return self.entity["title"]

    @property
    def gender(self) -> Optional[str]:
        """Return the gender of the entity, or None if it doesn't exist."""
        try:
            return self.get_property("P21").label
        except KeyError:
            return None

    @property
    def nationality(self) -> Optional[str]:
        """
        Return the nationality, or None if it doesn't exist.

        The nationality can either be an ISO 3166-1 alpha-2 code, or the full
        name of the country if the former doesn't exist.
        """
        try:
            e = self.get_property("P27")
        except KeyError:
            return None

        try:
            return e.get_property("P297")
        except KeyError:
            # TODO: try a bit harder
            pass

        # use the name by default
        return _uc_first(e.label)

    def get_property(self, name: str):
        """Return property $prop, in a hopefully useful form."""
        prop = self.entity["claims"][name][0]["mainsnak"]["datavalue"]

        if prop["type"] == "string":
            return prop["value"].lower()
        elif prop["type"] == "wikibase-entityid":
            return entity(prop["value"]["id"])

        return prop["value"]

    @property
    def label(self) -> str:
        """Return the label."""
        return self.entity["labels"]["en"]["value"]

    @property
    def description(self) -> str:
        """Return the description."""
        try:
            return _uc_first(self.entity["descriptions"]["en"]["value"])
        except KeyError:
            return ""


################################################################################


def fetch_entities(qids):
    """Make a best-effort attempt to retrieve the entities with these QIDs."""
    for index, qid in qids.items():
        try:
            e = entity(qid)
        except json.decoder.JSONDecodeError as exc:
            print(f"Error: {qid}: {exc}")
            continue  # FIXME or retry?

        yield {
            "AuthorId": index,
            "QID": e.qid,
            "Author": e.label,
            "Nationality": e.nationality,
            "Gender": e.gender,
            "Description": e.description,
        }


################################################################################

if __name__ == "__main__":
    from pprint import pprint

    pprint(entity(sys.argv[1]).__dict__)
