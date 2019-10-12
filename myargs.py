from argparse import ArgumentParser
from importlib import import_module

# declare options
parser = ArgumentParser(description='convert OH1 KNX config to OH2 equivilant')
parser.add_argument('-c', '--config_file',
                    nargs='?',
                    default='config',
                    action='store',
                    help='Specify config filename without extension ".py" (default: %(default)s[.py])')
args = parser.parse_args()

# read in (custom) config file
try:
    config = import_module(args.config_file)
except ImportError as err:
    print(f'Error: {err}[.py]')
    exit(1)
