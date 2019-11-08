# vim: ts=4 : sw=4 : et

import yaml


# value = config('key.name')
def config(key):
    with open('data/config.yml') as fh:
        config = yaml.load(fh)

    for key in key.split('.'):
        try:
            config = config[key]
        except KeyError:
            # use defaults and/or emit warning
            return None

    return config


if __name__ == "__main__":
    import sys
    print(config(sys.argv[1]))

