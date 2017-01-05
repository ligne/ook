# -*- coding: utf-8 -*-

import time
import yaml
from xml.etree import ElementTree


# basic operations on a GR xml entity
class GRTree():
    # load the config to get the GR API key.
    with open('data/config.yml') as fh:
        config = yaml.load(fh)

    def __init__(self, grid, entity='book'):
        import requests

        r = requests.get('https://www.goodreads.com/{}/show/{}.xml'.format(entity, grid), params={
            'key': self.config['GR Key'],
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
