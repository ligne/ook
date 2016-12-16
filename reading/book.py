# -*- coding: utf-8 -*-

import sys

import reading.cache
from reading.author import Author
from reading._entity import Entity


# represents a book and its properties.
class Book():
    _qids = reading.cache.load_yaml('books_q')
    _names = reading.cache.load_yaml('books_n')
    _items = dict([(n, _qids.get(q, {})) for (n, q) in _names.iteritems()])

    # publication date, original language? previous/subsequent books?
    # series/entry:
    #   https://www.wikidata.org/wiki/Q769001
    #   https://www.wikidata.org/wiki/Q962265
    _fields = (
        'QID',
        'Name',
        'Description',
        'URL',
        'Author',
    )

    def __init__(self, name, author, language):
        self.name = name
        self._subj = None
        self._item = self._items.get(name, {})
        # FIXME can have more than one author.
        # https://www.wikidata.org/wiki/Q861461
        #
        # FIXME combine all author QIDs into one string. then short stories
        # won't upset the duplicates test.
        self._author = Author(author)
        self._language = language


    # like a dictionary's get() method.  FIXME warn if it's not a known one?
    def get(self, field, *args):
        return self._item.get(field, *args)


    # returns a list of missing fields for this book
    def missing_fields(self):
        return [f for f in self._fields if f not in self._item]


    # fetch any missing fields and report this in a pretty format
    def fetch_missing(self):
        # work out if anything is missing
        missing = self.missing_fields()
        if not missing:
            return

        # first, need to work out who we're talking about
        if not self._find():
            return

        # print the author's name before the first new field.
        print self.name

        for field in missing:
            # save the field, and print it.
            self._item[field] = self.get_field(field)
            print '{:12s} - {}'.format(field, self.get(field))

        # make sure the book cache gets updated.
        self._qids[self.get('QID')] = self._item
        self._names[self.name] = self.get('QID')

        print


    # searches for the author if necessary.
    def _find(self):
        if not self.get('QID'):
            self._search()
            # give up if nothing could be found.
            if not self.get('QID'):
                print "Couldn't find {}".format(self.name)  # FIXME
                print
                return 0
        return 1


    # loads the entity if necessary.
    def _load_entity(self):
        # now get the entity from the server, if we don't already have it.
        if not self._subj:
            self._subj = self._get_entity(self.get('QID'))
        return


    # searches for the book and caches the result.
    # FIXME try tweaking the title to get a better match.  anything after a / or ;.
    #
    # split on:
    #   ' / '
    #   '; '
    #   ': '
    #   ' - '
    #   ', '
    #   ', a'
    #   ' — '
    # anything in brackets at the end (square or round).
    def _search(self):
        results = self._request(action='wbsearchentities', search=self.name, language=self._language)['search']

        if not len(results):
            return

        candidates = []

        for res in results:
            if 'disambiguation page' in res.get('description', ''):
                continue

            subj = self._get_entity(res['id'])
            score = 0

            try:
                print subj.get_label(language=self._language)
            except:
                print '-'
            print str(res.get('description', '').encode('utf-8'))
            print res['concepturi']
            print

            # FIXME check P50 against author QID and/or name.

            instanceof = [ x['mainsnak']['datavalue']['value']['id'] for x in subj._subj['claims'].get('P31') or [] ]
            for qid in ['Q571', 'Q7725634', 'Q49084', 'Q8261', 'Q192782', 'Q35760']:
                if qid in instanceof:
                    score += 1

            if score >= 2:
                break

            if score > 0:
                candidates.append((score, subj))
            subj = None

        # return the most likely candidate (earliest result with the highest score)
        if not subj:
            if not candidates:
                return
            subj = sorted(candidates, key=lambda x: -x[0])[0][1]
        # save the QID, and cache the subject since we have it.
        self._item['QID'] = subj.get_qid()
        self._subj = subj

        return


    # fetches the subject data for entity $qid
    def _get_entity(self, qid):
        return Entity(self._request(action='wbgetentities', ids=qid)['entities'][qid])


    # runs a query against the API
    def _request(self, action='', search='', ids='', language='en'):
        import requests
        import time
        q = {
            'action': action,
            'language': language,
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
    # FIXME check aliases for a closer match?
    def _get_name(self):
        return self._subj.get_label(language=self._language)


    # returns the description of the subject.
    def _get_description(self):
        return self._subj.get_description()


    # returns the name of the author.
    # FIXME save the author:  create new Author object, run usual update on it.
    # can pass in the QID to skip the searching.
    def _get_author(self):
        return self._get_entity(self._get_property('P50')).get_label(self._language)


    # returns the URL to the entity.
    def _get_url(self):
        return 'http://www.wikidata.org/entity/{}'.format(self._subj.get_qid())


    # look up a field in the author blob.
    def get_field(self, field):
        try:
            self._load_entity()
            return str(getattr(self, '_get_' + field.lower().replace(' ', '_'))())
        except KeyError:
            return


    # saves all the caches at the end.
    @staticmethod
    def save():
        reading.cache.dump_yaml('books_n', Book._names)
        reading.cache.dump_yaml('books_q', Book._qids)


# vim: ts=4 : sw=4 : et
