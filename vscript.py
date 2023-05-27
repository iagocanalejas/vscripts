import argparse
import logging
import os
import sys

from commands import atempo, delay, hasten, extract

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))

COMMAND_ORDER = ['extract', 'atempo', 'delay', 'hasten']
COMMANDS = {
    'atempo': atempo,
    'delay': delay,
    'hasten': hasten,
    'extract': extract,
}


def _parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('path', help='path to be handled')
    parser.add_argument('actions', type=str, nargs='*', help='list of actions to be ran')
    parsed = parser.parse_args()

    todo = {}
    for action in parsed.actions:
        if '=' in action:
            a, v = action.split('=')
            todo[a] = v
        else:
            todo[action] = None

    return parsed, todo


if __name__ == '__main__':
    args, actions = _parse_arguments()
    logger.info(f'{os.path.basename(__file__)}:: args -> {args.__dict__}')
    logger.info(f'{os.path.basename(__file__)}:: actions -> {actions}')

    if any(k not in COMMAND_ORDER for k in actions.keys()):
        raise Exception(f'invalid command={next(k not in COMMANDS.keys() for k in actions.keys())}')

    processing_file = args.path
    for command in filter(lambda c: c in actions.keys(), COMMAND_ORDER):
        processing_file = COMMANDS[command](processing_file, actions[command]) \
            if actions[command] is not None \
            else COMMANDS[command](processing_file)
