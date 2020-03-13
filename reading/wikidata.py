# vim: ts=4 : sw=4 : et

"""Functions for interfacing with WikiData."""

import json
import sys

import requests


# uppercases the first character of $s *only*
def _uc_first(s):
    return s[:1].upper() + s[1:]


def wd_search(term):
    """Search for $term using the basic WikiData search."""
    return _format_search_results(requests.get("https://www.wikidata.org/w/api.php", params={
        "action": "wbsearchentities",
        "language": "en",
        "format": "json",
        "search": term,
    }).json())


def _format_search_results(results):
    return [{
        "Label": res["label"],
        "QID": res["id"],
        "Description": _uc_first(res.get("description", "")),
    } for res in results["search"]]


###############################################################################

# basic operations on an entity.
class Entity():

    # fetches an entity by its QID
    def __init__(self, qid):
        fname = 'data/cache/wikidata/{}.json'.format(qid)
        try:
            with open(fname) as fh:
                j = json.load(fh)
        except FileNotFoundError:
            url = 'https://www.wikidata.org/wiki/Special:EntityData/{}.json'.format(qid)
            r = requests.get(url)
            with open(fname, 'wb') as fh:
                fh.write(r.content)
            j = r.json()
        self.entity = j['entities'][qid]

    # handle non-humans and collectives
    def gender(self):
        return self.property('P21').label()

    # return a list if necessary
    def nationality(self):
        e = self.property('P27')

        # use the name by default
        nat = e.label()

        if e.has_property('P297'):
            nat = e.property('P297').lower()
        # TODO: try a bit harder

        return nat

    # whether the entity has the given property
    def has_property(self, prop):
        return prop in self.entity['claims']

    # returns the given property, in a hopefully useful form
    def property(self, prop):
        p = self.entity['claims'][prop][0]['mainsnak']['datavalue']

        if p['type'] == 'string':
            return p['value'].lower()
        elif p['type'] == 'wikibase-entityid':
            return Entity(p['value']['id'])

        return p['value']

    # returns the entity's label
    def label(self):
        return self.entity['labels']['en']['value']


################################################################################

if __name__ == '__main__':
    from pprint import pprint
    print(pprint(Entity(sys.argv[1])))

