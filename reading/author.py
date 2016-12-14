# -*- coding: utf-8 -*-

import sys
import time

import reading.cache


# basic operations on an entity.
class Entity():
    def __init__(self, subj):
        self._subj = subj


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


class Author():
    _qids = reading.cache.load_yaml('authors_q')
    _names = reading.cache.load_yaml('authors_n')
    _items = dict([(n, _qids.get(q, {})) for (n, q) in _names.iteritems()])

    _fields = (
        'QID',
        'Name',
        'Description',
        'Gender',
        'Nationality',
    )
    _nationalities = reading.cache.load_yaml('nationalities')
    _genders = reading.cache.load_yaml('genders')


    def __init__(self, name):
        name = ' '.join(name.split())  # normalise whitespace
        self.name = name
        self._subj = None
        self._item = self._items.get(name, {})
        # will be set to true if and when the name/description is printed out.
        self._issued_info = False


    # like a dictionary's get() method.  FIXME warn if it's not a known one?
    def get(self, field, *args):
        return self._item.get(field, *args)


    # returns a list of missing fields for this author
    def missing_fields(self):
        return [ f for f in self._fields if f not in self._item ]


    # fetch any missing fields and report this in a pretty format
    def fetch_missing(self):
        missing = self.missing_fields()

        for field in self.missing_fields():
            # first, need to work out who we're talking about
            if not self.get('QID'):
                self._search()
                # give up if nothing could be found.
                if not self.get('QID'):
                    print "Couldn't find {}".format(self.name)  # FIXME
                    print
                    return

            # now get the entity from the server, if we don't already have it.
            if not self._subj:
                self._subj = self._get_entity(self.get('QID'))

            # print the author's name before the first new field.
            if not self._issued_info:
                print self.name
                self._issued_info = True

            # now save the field, and print it.
            self._item[field] = self.get_field(field)
            print '{:12s} - {}'.format(field, self.get(field))

        # make sure the authors cache gets updated.
        self._qids[self.get('QID')] = self._item
        self._names[self.name] = self.get('QID')

        if missing:
            print


    # searches for the author and caches the result.
    def _search(self):
        results = self._request(action='wbsearchentities', search=self.name)['search']

        if not len(results):
            return

        candidates = []

        # check each entry for person-ness
        # FIXME also look for non-person writers (eg. collaborations)
        for res in results:
            if 'disambiguation page' in res.get('description', ''):
                continue

            subj = self._get_entity(res['id'])
            score = 0

            occupations = [ x['mainsnak']['datavalue']['value']['id'] for x in subj._subj['claims'].get('P106') or [] ]

            for qid in list(set(['Q36180', 'Q482980', 'Q28389', 'Q1930187', 'Q6625963', 'Q49757', 'Q214917', 'Q15980158', 'Q21036234'])):
                if qid in occupations:
                    score += 1

            instanceof = [ x['mainsnak']['datavalue']['value']['id'] for x in subj._subj['claims'].get('P31') or [] ]
            for qid in ['Q5', 'Q1690980']:
                if qid in instanceof:
                    score += 1

            candidates.append((score, subj))
            if score >= 3:
                break
            else:
                subj = None

        # return the most likely candidate (earliest result with the highest score)
        if not subj:
            subj = sorted(candidates, key=lambda x: -x[0])[0][1]
        # save the QID, and cache the subject since we have it.
        self._item['QID'] = subj.get_qid()
        self._subj = subj

        return


    # fetches the subject data for entity $qid
    def _get_entity(self, qid):
        return Entity(self._request(action='wbgetentities', ids=qid)['entities'][qid])


    # runs a query against the API
    def _request(self, action='', search='', ids=''):
        import requests
        q = {
            'action': action,
            'language': 'en',
            'format': 'json',
            'search': search,
            'ids': ids,
        }

        r = requests.get('https://www.wikidata.org/w/api.php', q)
        time.sleep(0.5)

        return r.json()


    # returns a property of the subject blob.
    def _get_property(self, prop):
        return self._subj.get_property(prop)


    # returns the QID of the subject.
    def _get_qid(self):
        return self._subj.get_qid()


    # returns the name of the subject.
    def _get_name(self):
        return self._subj.get_label()


    # returns the description of the subject.
    def _get_description(self):
        return self._subj.get_description()


    # returns the subject's gender.
    def _get_gender(self):
        p = self._get_property('P21')

        if p in self._genders:
            return self._genders[p]

        gender = self._get_entity(p).get_label()

        self._genders[p] = gender.lower()

        return self._genders.get(p)


    # returns the subject's nationality as a two-letter code.
    #
    # FIXME doesn't work with old countries that don't have a code.
    # could either try and look up the most recent equivalent, or just
    # use its QID
    def _get_nationality(self):
        p = str(self._get_property('P27'))

        if p in self._nationalities:
            return self._nationalities[p]

        country = self._get_entity(p)
        try:
            country = country.get_property('P297').lower()
        except KeyError:
            country = country.get_label()

        self._nationalities[p] = country

        return self._nationalities.get(p)


    # look up a field in the author blob.
    def get_field(self, field):
        try:
            return str(getattr(self, '_get_' + field.lower())())
        except KeyError:
            return


    # saves all the caches at the end.
    @staticmethod
    def save():
        reading.cache.dump_yaml('authors',       Author._items)  # FIXME unneeded
        reading.cache.dump_yaml('authors_n',     Author._names)
        reading.cache.dump_yaml('authors_q',     Author._qids)
        reading.cache.dump_yaml('nationalities', Author._nationalities)
        reading.cache.dump_yaml('genders',       Author._genders)

# vim: ts=4 : sw=4 : et
