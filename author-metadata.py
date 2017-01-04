#!/usr/bin/python

import sys

import reading
import reading.ebooks
from reading.author import Author
from reading.book import Book


df = reading.ebooks.get_books(fix_names=False)

for ix, book in df.iterrows():
    try:
        b = Book(book['Title'], book['Author'], book['Language'])
        b.fetch_missing()
        if len(b.get('AQIDs', [])) == 1:
            Author(book['Author'], qid=b.get('AQIDs')[0])
    except Exception as e:
        print e

################################################################################

df = reading.get_books(fix_names=False)

df = reading.on_shelves(df, [
    'read',
    'currently-reading',
    'pending',
    'elsewhere',
    'ebooks',
])

df1 = reading.ebooks.get_books(fix_names=False)

df = df.append(df1)

authors = sorted(df.Author.unique())

for author in authors:
    try:
        Author(author).fetch_missing()
    except Exception as e:
        print e

Book.save()
Author.save()


# vim: ts=4 : sw=4 : et
