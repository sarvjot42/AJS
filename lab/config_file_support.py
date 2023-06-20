import argparse
import os
import json


def parse_args():
    parser = argparse.ArgumentParser(description='A command line tool with config file support.')
    parser.add_argument('-c', '--config', dest='config_file', help='Path to the config file.')
    parser.add_argument('--generate-config', action='store_true', help='Generate a default config file.')
    args = parser.parse_args()

    if args.generate_config:
        with open('ast_config.json', 'w') as f:
            json.dump({}, f)

    return args


def main():
    args = parse_args()

    if args.config_file:
        config_file = args.config_file
    else:
        config_file = os.path.expanduser('~/ast_config.json')

    with open(config_file, 'r') as f:
        config = json.load(f)

    print(config)


if __name__ == '__main__':
    main()
