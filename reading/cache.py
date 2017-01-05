# -*- coding: utf-8 -*-

import yaml


# FIXME shouldn't specify yaml...

# returns a yaml data file's contents in a usable format.
def load_yaml(name, default=None):
    try:
        with open('data/{}.yml'.format(name)) as fh:
            return yaml.load(fh)
    except:
        if default is not None:
            return default
        return {}


# saves as yaml in a vaguely readable form.
def dump_yaml(name, data):
    with open('data/{}.yml'.format(name), 'w') as fh:
        yaml.dump(data, stream=fh, default_flow_style=False, encoding='utf-8', allow_unicode=True)

# vim: ts=4 : sw=4 : et
