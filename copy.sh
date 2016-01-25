#!/bin/bash

kindle_dir=/run/media/mlb/Kindle/documents/
[ -d "$kindle_dir" ] || {
  echo Kindle not mounted.
  exit 1
}

for dir in articles books short-stories
do
  rsync -ha "$dir/" "$kindle_dir/$dir" "$@"                      \
        --remove-source-files --info=COPY,DEL,MISC,NAME,SYMSAFE  \
        --exclude-from excludes/articles                         \
        --exclude-from excludes/books                            \
        --exclude-from excludes/short-stories
done

