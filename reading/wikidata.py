# vim: ts=4 : sw=4 : et

import sys
import requests
import json


# uppercases the first character of $s *only*
def _uc_first(s):
    return s[:1].upper() + s[1:]


# use the basic wikidata search.
def wd_search(term):
    r = requests.get('https://www.wikidata.org/w/api.php', params={
        'action': 'wbsearchentities',
        'language': 'en',
        'format': 'json',
        'search': term,
    })

    return [{
        'Label': res['label'],
        'QID': res['id'],
        'Description': _uc_first(res.get('description', '')),
    } for res in r.json()['search']]


# use wikipedia full-text search.
def search_harder(term):
    r = requests.get('https://en.wikipedia.org/w/api.php', params={
        'action': 'query',
        'list': 'search',
        'prop': 'pageprops',
        'format': 'json',
        'srsearch': term,
    })
    return r.content.decode('utf-8')
    return [{

    } for res in r.json()['query']['search']]


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


    def has_property(self, prop):
        return prop in self.entity['claims']


    def property(self, prop):
        p = self.entity['claims'][prop][0]['mainsnak']['datavalue']

        if p['type'] == 'string':
            return p['value'].lower()
        elif p['type'] == 'wikibase-entityid':
            return Entity(p['value']['id'])

        return p['value']


    def label(self):
        return self.entity['labels']['en']['value']


################################################################################

if __name__ == '__main__':
    from pprint import pprint
    print(pprint(Entity(sys.argv[1])))

