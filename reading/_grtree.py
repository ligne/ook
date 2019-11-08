# -*- coding: utf-8 -*-

import time
import yaml
from xml.etree import ElementTree

from .config import config

# basic operations on a GR xml entity
class GRTree():

    def __init__(self, grid, entity='book'):
        import requests

        r = requests.get('https://www.goodreads.com/{}/show/{}.xml'.format(entity, grid), params={
            'key': config('goodreads.key'),
        })
        time.sleep(1)
        self._tree = ElementTree.fromstring(r.content)


    # returns the string at $path
    def get_text(self, path):
        return self._tree.find(path).text.encode('utf-8')


    # returns all the nodes at $path
    def get_values(self, path):
        return self._tree.findall(path)


# vim: ts=4 : sw=4 : et
