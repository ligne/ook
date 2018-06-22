# vim: ts=4 : sw=4 : et

import sys
import requests


# use the basic wikidata search.
def search(term):
        r = requests.get('https://www.wikidata.org/w/api.php', params={
            'action': 'wbsearchentities',
            'language': 'en',
            'format': 'json',
            'search': term,
        })

        return [{
            'Title': res['label'],
            'QID': res['id'],
            'Description': res.get('description', ''),
        } for res in r.json()['search']]


################################################################################

# fetches an entity by its QID
def get_entity(qid):
    r = requests.get('https://www.wikidata.org/wiki/Special:EntityData/{}.json'.format(qid))
    return r.json()['entities'][qid]


################################################################################

if __name__ == '__main__':
#    print(search(sys.argv[1]))
    from pprint import pprint
    print(pprint(get_entity(sys.argv[1])))
