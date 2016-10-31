#!/bin/sh

kindle_dir=/run/media/mlb/Kindle
[ -d "$kindle_dir" ] || {
  echo Kindle not mounted.
  exit 1
}

cd ~/ebooks/

# clean up cruft
./clean.py
echo

# copy any new files over
# FIXME nothing to do here yet

# take a backup
rsync -ha --delete $kindle_dir/ /home/local/mlb/.kindle/ --exclude-from ~/.kindle-excludes

# recalculate wordcounts
./wordcounts.py

# regenerate the graphs and update the total ebook wordcount
./reading.py

tmpdir=`mktemp -d`

# update suggestions
(
  echo All Books
  echo
  ./suggestions.py wordcounts/books-*-lengths.txt 15
  echo ----
  echo All short stories
  echo
  ./suggestions.py wordcounts/short-stories-*-lengths.txt 15
  echo ----
  echo French books
  echo
  ./suggestions.py wordcounts/*-fr-lengths.txt 15
  echo ----
  echo Non-fiction
  echo
  ./suggestions.py wordcounts/non-fiction-*-lengths.txt 15
) | cut -c-50 > $tmpdir/00\ Suggestions.txt

# add alphabetically and numerically sorted versions of all wordcount lists.
(
  echo Articles
  echo
  sort -nr wordcounts/articles-*-lengths.txt
  echo ----
  echo Books
  echo
  sort -nr wordcounts/books-*-lengths.txt
  echo ----
  echo Short stories
  echo
  sort -nr wordcounts/short-stories-*-lengths.txt
  echo ----
  echo French books
  echo
  sort -nr wordcounts/*-fr-lengths.txt
  echo ----
  echo Non-fiction
  echo
  sort -nr wordcounts/non-fiction-*-lengths.txt
) | cut -c-50 > $tmpdir/00\ Numeric.txt
(
  echo Articles
  echo
  sort -k2 wordcounts/articles-*-lengths.txt
  echo ----
  echo Books
  echo
  sort -k2 wordcounts/books-*-lengths.txt
  echo ----
  echo Short stories
  echo
  sort -k2 wordcounts/short-stories-*-lengths.txt
  echo ----
  echo French books
  echo
  sort -k2 wordcounts/*-fr-lengths.txt
  echo ----
  echo Non-fiction
  echo
  sort -k2 wordcounts/non-fiction-*-lengths.txt
) | cut -c-50 > $tmpdir/00\ Alphabetical.txt

diff -uwr $kindle_dir/documents/wordcounts/00\ Suggestions.txt $tmpdir/
rsync -ha --delete $tmpdir/ $kindle_dir/documents/wordcounts/

