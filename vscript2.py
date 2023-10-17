#!/usr/bin/env python3

import argparse
import logging
import os
import sys

from commands import append, append_subs, atempo, delay, extract, hasten

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))

COMMAND_ORDER = ["extract", "atempo", "delay", "hasten", "append", "subs"]
COMMANDS = {
    "atempo": atempo,
    "delay": delay,
    "hasten": hasten,
    "extract": extract,
    "append": append,
    "subs": append_subs,
}

# TODO: convert to Path when the file enters


def _parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="path to be handled")
    parser.add_argument("actions", type=str, nargs="*", help="list of actions to be ran")
    parsed = parser.parse_args()

    todo = {}
    for action in parsed.actions:
        if "=" in action:
            a, v = action.split("=")
            todo[a] = v
        else:
            todo[action] = None

    return parsed, todo


if __name__ == "__main__":
    args, actions = _parse_arguments()
    logger.info(f"{os.path.basename(__file__)}:: args -> {args.__dict__}")
    logger.info(f"{os.path.basename(__file__)}:: actions -> {actions}")

    if any(k not in COMMAND_ORDER for k in actions.keys()):
        raise Exception(f"invalid command={next(k not in COMMANDS.keys() for k in actions.keys())}")

    og_file = processing_file = args.path
    for command in filter(lambda c: c in actions.keys(), COMMAND_ORDER):
        fn = COMMANDS[command]
        arg = actions[command]

        if command == "append" and arg is None:
            processing_file = fn(og_file, processing_file)
            continue
        if arg is not None:
            processing_file = fn(processing_file, arg)
            continue
        processing_file = fn(processing_file)
