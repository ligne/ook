# -*- coding: utf-8 -*-

import sys
import re
from difflib import SequenceMatcher
from xml.etree import ElementTree

import reading.cache
from reading.author import Author
from reading._entity import Entity
from reading._grtree import GRTree


# represents a book and its properties.
class Book():
    _qids = reading.cache.load_yaml('books_q')
    _names = reading.cache.load_yaml('books_n')
    _items = reading.cache.load_yaml('books', [])

    # publication date, original language? previous/subsequent books?
    # series/entry:
    #   https://www.wikidata.org/wiki/Q769001
    #   https://www.wikidata.org/wiki/Q962265
    _fields = (
        'QID',
        'GRID',
        'Title',
        'GR Title',
        'Description',
        'URL',
        'GR URL',
        'AQIDs',
        'Authors',
        'AGRIDs',
        'GR Authors',
        'Language',
        'Original Publication Year',
        'Category',
    )

    def __init__(self, book, qid=None, grid=None):
        self.name = book['Title']
        self.author = book['Author']
        self._subj = None
        self._tree = None
        self._language = book['Language']

        qid = self._names.get(name)

        if qid:
            self._item = self._qids.get(qid, {'QID': qid})
            self._names[name] = qid
        else:
            self._item = {}


    # like a dictionary's get() method.  FIXME warn if it's not a known one?
    def get(self, field, d=None):
        return self._item.get(field) or d


    # returns a list of missing fields for this book
    def missing_fields(self):
        return [f for f in self._fields if f not in self._item]


    # fetch any missing fields and report this in a pretty format
    def fetch_missing(self):
        # work out if anything is missing
        missing = self.missing_fields()
        if missing:
            # first, need to work out who we're talking about
            if not self._find():
                return

            # print the author's name before the first new field.
            print self.name

            for field in missing:
                # save the field, and print it.
                self._item[field] = self.get_field(field)
                print '{:12.12s} - {}'.format(field, self.get(field))

            print

        # make sure the book cache gets updated.
        self._qids[self.get('QID')] = self._item
        if self.get('Name'):
            self._names[self.get('Name')] = self.get('QID')
        self._names[self.name] = self.get('QID')


    # searches for the author if necessary.
    def _find(self):
        if not self.get('QID'):
            self._search()
        if not self.get('GRID'):
            self._gr_search()
        # give up if nothing could be found.
        if not (self.get('QID') or self.get('GRID')):
            print "Couldn't find {}".format(self.name)  # FIXME
            print
            return 0
        return 1


    # loads the entities if necessary.
    def _load_entities(self):
        if not self._subj and self.get('QID'):
            self._subj = Entity(self.get('QID'))
        if not self._tree and self.get('GRID'):
            self._tree = GRTree(self.get('GRID'))
        return


    # searches for the book and caches the result.
    def _search(self):
        name = re.sub(r'\[\w+\]$', '', self.name)  # remove brackets
        name = re.split(r'[-/;:,—]\s+', name)[0]  # take everything up to the delimiter.
        # FIXME search for both this and the original

        results = self._request(action='wbsearchentities', search=name, language=self._language)['search']

        if not len(results):
            return

        candidates = []

        for res in results:
            if 'disambiguation page' in res.get('description', ''):
                continue

            subj = Entity(res['id'])
            score = 0

            # FIXME check P50 against author QID and/or name.

            try:
                instanceof = [ x['mainsnak']['datavalue']['value']['id'] for x in subj._subj['claims'].get('P31') or [] ]
            except AttributeError:
                instanceof = []
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

        r = requests.get('https://www.wikidata.org/w/api.php', params=q)
        time.sleep(0.5)

        return r.json()


    # returns a property of the subject blob.
    def _get_property(self, prop):
        return self._subj.get_property(prop)


    # returns the QID of the subject.
    def _get_qid(self):
        return self._subj.get_qid()


    # returns the GRID of the subject.
    def _get_grid(self):
        return self._tree.get_text('book/id')


    # returns the name of the subject.
    # FIXME check aliases for a closer match?
    def _get_title(self):
        try:
            return self._subj.get_label(language=self._language)
        except AttributeError:
            return self._get_gr_title()


    # returns the GR title
    def _get_gr_title(self):
        return self._tree.get_text('book/title')


    # returns the description of the subject.
    def _get_description(self):
        return self._subj.get_description()


    # returns the name(s) of the author(s).
    def _get_authors(self):
        for qid in self.get_field('AQIDs'):
            Author(qid=qid).fetch_missing()
        return ', '.join([ Author(qid=x).get('Name', x) for x in self._item.get('AQIDs') ])


    # returns a list of the QIDs for all the authors
    def _get_aqids(self):
        return [ str(x['mainsnak']['datavalue']['value']['id']) for x in self._subj._get_claims('P50') ]


    def _get_agrids(self):
        return [
            x.find('id').text.encode('utf-8')
                for x in self._tree.get_values('book/authors/author')
                if not x.find('role').text
        ]


    def _get_gr_authors(self):
        return ', '.join([
            x.find('name').text.encode('utf-8')
                for x in self._tree.get_values('book/authors/author')
                if not x.find('role').text
        ])


    # returns the URL for the entity.
    def _get_url(self):
        return 'http://www.wikidata.org/entity/{}'.format(self._subj.get_qid())


    # returns the GR URL for the entity.
    def _get_gr_url(self):
        return 'https://www.goodreads.com/book/show/{}'.format(self._tree.get_text('book/id'))


    # returns the language of the book.
    def _get_language(self):
        return self._tree.get_text('book/language_code')[:2]


    # returns the year the book was originally published
    def _get_original_publication_year(self):
        return self._tree.get_text('book/work/original_publication_year')


    # returns the category for the book.
    def _get_category(self):
        shelves = [ x.get('name') for x in self._tree.get_values('book/popular_shelves/shelf')]

        cats = [
            [ 'novels', 'novel', 'roman', 'romans', ],
            [ 'non-fiction', 'nonfiction', ],
            [ 'short-stories', 'graphic-novel', 'nouvelles', ],
        ]

        categories = []

        for c in cats:
            try:
                i = min([shelves.index(term) for term in c if term in shelves])
                categories.append((c[0], i))
            except (IndexError, ValueError):
                pass

        try:  # FIXME not really needed?  catch further up.
            return sorted(categories, key=lambda x: x[1])[0][0]
        except IndexError:
            return
    # look up a field in the author blob.
    def get_field(self, field):
        try:
            self._load_entities()
            return getattr(self, '_get_' + field.lower().replace(' ', '_'))()
        except (KeyError, TypeError, AttributeError):
            return


    # saves all the caches at the end.
    @staticmethod
    def save():
        reading.cache.dump_yaml('books_n', Book._names)
        reading.cache.dump_yaml('books_q', Book._qids)
        reading.cache.dump_yaml('books', Book._items)


    def _gr_search(self):
        import requests
        import time
        name = re.sub(r'\s?\[\w+\]$', '', self.name)  # remove brackets

        author = self.author

        r = requests.get('https://www.goodreads.com/search/index.xml', params={
            'key': '_____gOoDrEaDsKeY_____',
            'q': (name + ' ' + author).strip()
        })
        time.sleep(1)

        tree = ElementTree.fromstring(r.content)

        candidates = []

        for work in tree.findall('search/results/work/best_book'):
            # remove the series name blah blah first. also other cruft?
            # force to lower.
            title = str(work.find('title').text.encode('utf-8'))
            title = re.sub('(?P<Title>.+?)(?: ?\((?P<Series>.+?),? +#(?P<Entry>\d+)(?:; .+?)?\))?$', lambda x: x.group('Title'), title)
            tdist = SequenceMatcher(None, title.lower(), name.lower()).ratio()

            author = str(work.find('author/name').text.encode('utf-8'))
            adist = SequenceMatcher(None, author.lower(), str(self.author).lower()).ratio()

            grid = work.find('id').text

            score = tdist + adist

            if score < 1:
                continue

            candidates.append((score, grid))

        s = sorted(candidates, key=lambda x: -x[0])

        try:
            self._item['GRID'] = s[0][-1]
        except IndexError:
            pass

        return


# vim: ts=4 : sw=4 : et
