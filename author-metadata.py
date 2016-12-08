#!/usr/bin/python

import time

import reading
from reading.author import Author

df = reading.get_books()

df = reading.on_shelves(df, ['read', 'currently-reading', 'pending', 'elsewhere', 'ebooks'])

all_authors = sorted(list(set(df.Author.values)))

for authors in zip(*[iter(all_authors)]*10):
    for author in authors:
        Author(author).fetch_missing()


Author.save()

