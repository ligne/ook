#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import time
import yaml

import reading


# basic operations on an entity.
class Entity():
    def __init__(self, subj):
        self._subj = subj


    # returns the property $prop
    def get_property(self, prop):
        p = self._subj['claims'][prop]

        p = p[0]['mainsnak']['datavalue']['value']
        if type(p) == dict:
            p = p['id']

        return str(p)


    # returns the QID
    def get_qid(self):
        return str(self._subj['id'])


    # returns the label
    def get_label(self):
        return str(self._subj['labels']['en']['value'])


    # returns the description
    def get_description(self):
        return str(self._subj['descriptions']['en']['value']).capitalize()


class Author():
    _authors = reading.load_yaml('authors')
    _fields = (
        'QID',
        'Description',
        'Gender',
        'Nationality',
    )
    _nationalities = reading.load_yaml('nationalities')
    _genders = reading.load_yaml('genders')


    def __init__(self, name):
        self.name = name
        if name not in self._authors:
            self._authors[name] = {}
        self._author = self._authors[name]
        # will be set to true if and when the author name/description is
        # printed out.
        self._issued_info = False


    # like a dictionary's get() method.  FIXME warn if it's not a known one?
    def get(self, field):
        return self._author.get(field)


    # returns a list of missing fields for this author
    def missing_fields(self):
        return [ f for f in self._fields if f not in self._author ]


    # fetch any missing fields and report this in a pretty format
    def fetch_missing(self):
        for field in self.missing_fields():
            # first, need to work out who we're talking about
            if not self.get('QID'):
                self._search_author()
                # give up if nothing could be found.
                if not self.get('QID'):
                    print "Couldn't find {}".format(self.name)  # FIXME
                    return

            # now get the entity from the server, if we don't already have it.
            if not self._subj:
                self._subj = self._get_entity(self._get_qid())

            # print the author's name before the first new field.
            if not self._issued_info:
                print self.name
                self._issued_info = True

            # now save the field, and print it.
            self._author[field] = self.get_field(field)
            print '{:12s} - {}'.format(field, self.get(field))


    # searches for the author and caches the result.
    def _search_author(self):
        results = self._request(action='wbsearchentities', search=self.name)['search']

        # check each entry for person-ness
        # FIXME also look for "writer" occupation
        # for occupation in subj['claims']['P106']:
        #    print occupation['mainsnak']['datavalue']['value']['id'] == 'Q36180'
        # FIXME also look for non-person writers (eg. collaborations)
        for res in results:
            subj = self._get_entity(res['id'])
            for stmt in subj._subj['claims'].get('P31'):
                if stmt['mainsnak']['datavalue']['value']['id'] == 'Q5':
                    # save the QID, and cache the subject since we have it.
                    self._author['QID'] = subj.get_qid()
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





for name in ['Iain Banks', 'Ffeafe Reqttqa', 'Joseph Conrad']:
    author = Author(name)
    author.fetch_missing()
    print





################################################################################

sys.exit()

a = reading.load_yaml('authors')

# FIXME allow it to run in batches of $n unprocessed entries at a time.

df = reading.get_books()

for author in reading.read_since(df, '2015').Author.values:
    print author

#     au = Author(author)
#     au.get_info()


    # FIXME need to check that we have all the data we actually need...
    if author in a:
        print 'i know about {};  continuing'.format(author)
    else:
        # FIXME offer the ID as a hint.
        # FIXME what to do if the author can't be found at all?
        subj = author_item(author, a.get(author, {}).get('id'))
        if not subj:
            print
            continue
        # cache the ID too!
        print subj['id']

    info = a.get(author, {})

    # FIXME fetch the author blob in here instead?
    for field in ['Gender', 'Description', 'Nationality']:
        if not field in info:
            data = get_field(field, subj)
            if not data:
                print "Unable to retrieve {} for {}".format(field, author)
            info[field] = data
        #print '{:12s} - {}'.format(field, info[field])
    print

    a[author] = info


reading.dump_yaml('blah', a)

import subprocess
subprocess.call(['diff', '-uwr', 'data/authors.yml', 'data/blah.yml'])

print nationalities
reading.dump_yaml('nationalities', nationalities)

# vim: ts=4 : sw=4 : et
