import argparse
import logging
import os

from commands import atempo, delay, hasten, extract

COMMANDS = {
    'atempo': atempo,
    'delay': delay,
    'hasten': hasten,
    'extract': extract,
}


def _parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', help='command to be run')
    parser.add_argument('path', help='path to be handled')
    args, extra = parser.parse_known_args()

    extra = {v.split("=")[0]: v.split("=")[1] for v in extra}
    return args, extra


if __name__ == '__main__':
    args, kwargs = _parse_arguments()
    logging.info(f'{os.path.basename(__file__)}:: args -> {args.__dict__}')
    logging.info(f'{os.path.basename(__file__)}:: extras -> {kwargs}')

    if args.command not in COMMANDS.keys():
        raise Exception(f'invalid command={args.command}')

    COMMANDS[args.command](args.path, **kwargs)
