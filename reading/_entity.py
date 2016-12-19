# -*- coding: utf-8 -*-

import sys
import time


# basic operations on an entity.
class Entity():

    def __init__(self, qid):
        import requests

        r = requests.get('https://www.wikidata.org/wiki/Special:EntityData/{}.json'.format(qid))
        time.sleep(1)

        self._subj = r.json()['entities'][qid]


    # returns the property $prop
    def get_property(self, prop):
        p = self._get_claims(prop)

        p = p[0]['mainsnak']['datavalue']['value']
        if type(p) == dict:
            p = p['id']

        return str(p)


    # returns the QID
    def get_qid(self):
        return str(self._subj['id'])


    # returns the label
    def get_label(self, language='en'):
        return str(self._subj['labels'][language]['value'].encode('utf-8'))


    # returns the description
    def get_description(self):
        s = str(self._subj['descriptions']['en']['value'].encode('utf-8'))
        return s[0].upper() + s[1:]


    # returns the list of claims of type $prop
    def _get_claims(self, prop):
        return self._subj['claims'][prop]


# vim: ts=4 : sw=4 : et
