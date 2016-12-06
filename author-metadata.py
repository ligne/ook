#!/usr/bin/python

import reading
from reading.author import Author

df = reading.get_books()

all_authors = list(set(df.Author.values))

for authors in zip(*[iter(all_authors)]*1):
    for author in authors:
        Author(author).fetch_missing()
        print
    print
    break


