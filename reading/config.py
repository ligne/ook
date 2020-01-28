# vim: ts=4 : sw=4 : et

import yaml


# value = config('key.name')
def config(key):
    with open('data/config.yml') as fh:
        conf = yaml.safe_load(fh)

    for segment in key.split('.'):
        try:
            conf = conf[segment]
        except KeyError:
            # use defaults and/or emit warning
            return None

    return conf


################################################################################

def main(args):
    print(config(args.key))

