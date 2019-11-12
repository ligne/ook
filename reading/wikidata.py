# vim: ts=4 : sw=4 : et

import sys
import requests


# use the basic wikidata search.
def wd_search(term):
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

# fetches an entity by its QID
def get_entity(qid):
    r = requests.get('https://www.wikidata.org/wiki/Special:EntityData/{}.json'.format(qid))
    return r.json()['entities'][qid]


################################################################################

if __name__ == '__main__':
#    print(search(sys.argv[1]))
    from pprint import pprint
    print(pprint(get_entity(sys.argv[1])))

