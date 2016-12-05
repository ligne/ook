#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import time
import yaml

import reading


class Author():
    _authors = reading.load_yaml('authors')
    _fields = (
        'QID',
        'Description',
        'Gender',
        'Nationality',
    )


    def __init__(self, name):
        self.name = name
        self._author = self._authors.get(name, {})
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
            for stmt in subj['claims'].get('P31'):
                if stmt['mainsnak']['datavalue']['value']['id'] == 'Q5':
                    # save the QID, and cache the subject since we have it.
                    self._author['QID'] = str(res['id'])
                    self._subj = subj
                    return


    # fetches the subject data for entity $qid
    def _get_entity(self, qid):
        return self._request(action='wbgetentities', ids=qid)['entities'][qid]


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
    def _get_property(self, prop, subj=None):
        if not subj:
            subj = self._subj

        p = subj['claims'][prop]

        if prop == 'P297':
            return p[0]['mainsnak']['datavalue']['value']

        return p[0]['mainsnak']['datavalue']['value']['id']


    # returns the QID of the subject.
    def _get_qid(self):
        return self._subj['id']


    # returns the description of the subject.
    def _get_description(self):
        return self._subj['descriptions']['en']['value']


    # returns the subject's gender.
    def _get_gender(self):
        pass


    # returns the subject's nationality as a two-letter code.
    def _get_nationality(self):
        pass


    # look up a field in the author blob.
    def get_field(self, field):
        return str(getattr(self, '_get_' + field.lower())())





for name in ['Iain Banks', 'Ffeafe Reqttqa', 'Joseph Conrad']:
    author = Author(name)
    author.fetch_missing()
    print





################################################################################

# returns the author's gender.
#
# FIXME should look it up from a cache, like author_nationality does.
def author_gender(author):
    genders = {
        'Q6581097': 'male',
        'Q6581072': 'female',
    }
    return genders.get(_get_property(author, 'P21'), '')


# returns the author's nationality as a two-letter code thing.
#
# FIXME doesn't work with old countries that don't have a code.  could either
# try and look up the most recent equivalent, or just use the Q code.
#
# FIXME looks like this would all be a lot better as an Author class...
nationalities = reading.load_yaml('nationalities')

def author_nationality(author):
    p = _get_property(author, 'P27')
    if not p:
        return

    p = str(p)

    if p in nationalities:
        return nationalities[p]

    country = _get_entity(p)
    country = _get_property(country, 'P297')

    if country:
        nationalities[p] = str(country).lower()

    return nationalities.get(p)


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
