#!/usr/bin/python

import reading
import reading.ebooks
from reading.author import Author

df = reading.get_books(fix_names=False)

df = reading.on_shelves(df, ['read', 'currently-reading', 'pending', 'elsewhere', 'ebooks'])

df1 = reading.ebooks.get_books(fix_names=False)

df = df.append(df1)

authors = sorted(df.Author.unique())

for author in authors:
    try:
        Author(author).fetch_missing()
    except Exception as e:
        print e
        continue

Author.save()

