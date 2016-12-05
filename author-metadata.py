#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import requests
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


    # like a dictionary's get() method.  FIXME warn if it's not a known one?
    def get(self, field):
        return self._author.get(field)


    # returns a list of missing fields for this author
    def missing_fields(self):
        return [ f for f in self._fields if f not in self._author ]


    # fetch any missing fields and report this in a pretty format
    def fetch_missing(self):
        for field in self.missing_fields():
            print self._author  # FIXME debugging

            # first, need to work out who we're talking about
            if not self.get('QID'):
                self._search_author()


    # searches for the author and caches the result.
    def _search_author():
        r = requests.get('https://www.wikidata.org/w/api.php', {
            'action': 'wbsearchentities',
            'search': author,
            'language': 'en',
            'format': 'json',
        })
        time.sleep(0.5)

        # check each entry for person-ness
        # FIXME also look for "writer" occupation
        # for occupation in subj['claims']['P106']:
        #    print occupation['mainsnak']['datavalue']['value']['id'] == 'Q36180'
        # FIXME also look for non-person writers (eg. collaborations)
        for res in r.json()['search']:
            subj = _get_entity(res['id'])
            for stmt in subj['claims'].get('P31'):
                if stmt['mainsnak']['datavalue']['value']['id'] == 'Q5':
                    self._author['QID'] = res['id']
                    self._subj = subj



for name in ['Iain Banks', 'Ffeafe Reqttqa']:
    print name
    author = Author(name)
    print author.missing_fields()
    print author.get('Nationality')
    print





################################################################################

# searches for entity $subj (a Q\d+ code) and returns the actual subject data.
def _get_entity(subj):
    r = requests.get('https://www.wikidata.org/w/api.php', {
        'action': 'wbgetentities',
        'ids': subj,
        'languages': 'en',
        'format': 'json',
    })
    time.sleep(0.5)

    return r.json()['entities'][subj]


# returns a property of $entity.
# FIXME should explode.  can catch errors further up.
def _get_property(author, prop):
    p = author['claims'].get(prop)
    if not p:
        return None

    if prop == 'P297':
        return p[0]['mainsnak']['datavalue']['value']

    return p[0]['mainsnak']['datavalue']['value']['id']


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


# description field of the author blob.  make it clearer if it's found the
# wrong person.
def author_description(subj):
    return subj['descriptions']['en']['value']


# look up a field on the author blob.
n = __import__(__name__)
def get_field(field, subj):
    for f in [x for x in dir(n) if x.startswith('author_' + field.lower())]:
        return str(getattr(n, f)(subj))


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
