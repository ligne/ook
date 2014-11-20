#!/usr/bin/python

import sys, os, glob, subprocess, re, time
import tempfile
import shelve
import json
import pickle
import hashlib

sys.path.insert(0, '/usr/lib64/calibre')
sys.resources_location = os.environ.get('CALIBRE_RESOURCES_PATH', '/usr/share/calibre')
sys.extensions_location = os.environ.get('CALIBRE_EXTENSIONS_PATH', '/usr/lib64/calibre/calibre/plugins')
sys.executables_location = os.environ.get('CALIBRE_EXECUTABLES_PATH', '/usr/bin')

from calibre.ebooks.metadata.meta import get_metadata


### some basic initialisation

DEVNULL = open(os.devnull, 'w')

# open the collections
with open(os.environ['HOME'] + '/.kindle/system/collections.json') as c:
        coll = json.load(c)

# cache word-counts
wcs = shelve.open(os.environ['HOME'] + '/.wordcounts.pickle')


### Functions and stuff

def file_infos(path, ext):
        if path not in wcs:
                wcs[path] = wordcount(path)
        words = wcs[path]

        author, title = metadata(path, ext)

        return {
                'title':  title,
                'author': author,
                'words': words,
        }


def wordcount(path):
        if subprocess.call(['ebook-convert', path, '/tmp/test.txt'], stdout=DEVNULL, stderr=DEVNULL):
                return

        words = 0
        with open('/tmp/test.txt', 'r') as book:
                for line in book:
                        words += len(line.split(None))

        return words


def metadata(path, ext):
        # metatdata
        stream = open(path, 'r+b')

        try:
                mi = get_metadata(stream, ext, force_read_metadata=True)
        except:
                return

        title  = re.sub(r'\n', ' ', re.sub(r'^(the|a|le|la|les) ', '', mi.get('title'), flags=re.I).expandtabs())
        author = re.sub(r'\n', ' ', mi.get('authors')[0])

        return (author, title)


def book_pages(author, title):
        # clean up the author
        author = re.sub('\d+-\d+', '', author)

        pages = try_lookup(author, title) or try_lookup(title, author)
        return pages


#import requests
def try_lookup(author, title):
        url = 'https://openlibrary.org/search.json'
        params = dict(
                author = author,
                title  = title,
        )

        resp = requests.get(url=url, params=params)
        print resp.request.url

        j = resp.json()

        if not j['num_found']:
                return

        for olid in j['docs'][0]['edition_key']:
                time.sleep(1)

                resp = requests.get(url='https://openlibrary.org/books/' + olid + '.json')
                print resp.request.url
                j = resp.json()
                if 'number_of_pages' in j:
                        return j['number_of_pages']

        return None


def print_entry(fi, filehandle=sys.stdout):
        if fi and fi['words'] is not None:
                fh.write('{words}\t{title}'.format(**fi))
                if fi['author'] != 'Unknown':
                        fh.write(' ({author})'.format(**fi))
                fh.write('\n')
        #print fi['title'], fi['author']



def collection_lookup(key, f):
	ret = None
        for n, c in coll.items():
                if key in c['items']:
                        cname = re.split(r'@', n, maxsplit=1)
			if ret:
				print "{} is in {} as well as {}".format(f, cname[0], ret)
                        ret = cname[0]
        return ret


def get_collection(f):
        # hash of the filename
        HASH_PREFIX = "/mnt/us/documents/"
        key = "*%s" % hashlib.sha1("/mnt/us/documents/%s" % os.path.basename(f)).hexdigest()
        c = collection_lookup(key, f)
        if c:  return c

        # documents sent via amazon.
        asin = re.search(r'-asin_([A-Z0-9]+)-type_([A-Z]+)-', f)
        if asin:
                key = '#{}^{}'.format(*asin.groups())
                c = collection_lookup(key, f)
        if c:  return c

        # embedded asin identifier
        stream = open(f, 'r+b')
        try: mi = get_metadata(stream, 'mobi', force_read_metadata=True)
        except: pass
        if mi and mi.has_identifier('mobi-asin'):
                # EBOK suffix
                key = '#{}^{}'.format(mi.get_identifiers()['mobi-asin'], 'EBOK')
                c = collection_lookup(key, f)
                if c:  return c
                # PDOC suffix
                key = '#{}^{}'.format(mi.get_identifiers()['mobi-asin'], 'PDOC')
                c = collection_lookup(key, f)

        return c


# main

if len(sys.argv) > 1:
        # if arg:  process that file.  else process all.
        fi = file_infos(sys.argv[1], 'mobi')
        if fi:
                print '{words}\t{title} ({author})'.format(**fi)
                #pages = book_pages(fi['author'], fi['title'])
                words = fi['words']
                print 'pages:\t{0}-{1}'.format(words/400, words/250)
                #print pages
                #print 'words per page: ', fi['words'] / pages
else:
        d = tempfile.mkdtemp() + '/'

        fhs = {
                'later':          open(d + '/article-lengths-later.txt', 'w'),
                'books':          open(d + '/book-lengths-later.txt', 'w'),
                'short stories':  open(d + '/book-lengths-shortstories.txt', 'w'),
        }

        # books
        fh_no = open(d + '/book-lengths.txt', 'w')
        for ext in 'prc', 'mobi', 'txt':
                for f in glob.glob(os.environ['HOME'] + '/.kindle/documents/*.' + ext):
                        c = get_collection(f)
                        fh = fhs.get(c, fh_no)
                        print_entry(file_infos(f, 'mobi'), fh)
        fh_no.close()

        # articles
        fh_no = open(d + '/article-lengths.txt', 'w')
        for ext in 'azw', 'azw3':
                for f in glob.glob(os.environ['HOME'] + '/.kindle/documents/*.' + ext):
                        c = get_collection(f)
                        fh = fhs.get(c, fh_no)
                        print_entry(file_infos(f, 'mobi'), fh)
        fh_no.close()

        for fh in fhs.values():
                fh.close()

        # reset the colours, because ffs calibre.
        sys.stderr.write('\033[0m')

        dest = os.environ['HOME'] + '/wordcounts/'

        # show the diff
        subprocess.call(['diff', '-uwr', dest, d])

        # move the new files into place
        subprocess.call(['rsync', '-ha', '--delete', '--remove-source-files', d, dest])

