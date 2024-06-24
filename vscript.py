#!/usr/bin/env python3

import argparse
import json
import logging
import os
import sys
from pathlib import Path

from vscripts.commands import append, append_subs, atempo, delay, extract, hasten
from vscripts.constants import FRAME_RATE

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


def main(path_name: str, actions: dict[str, str]):
    path = Path(path_name).absolute()
    og_file = Path(path_name).absolute()
    assert path.is_file()

    for command in filter(lambda c: c in actions.keys(), COMMAND_ORDER):
        fn = COMMANDS[command]
        arg = actions[command]

        if command == "append" and arg is None:
            # condition when we append a file at the end of a command queue
            path = fn(path, into=og_file)
            continue
        if arg is not None:
            path = fn(path, arg)
            continue
        path = fn(path)


def _parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="path to be handled")
    parser.add_argument("actions", type=str, nargs="*", help="list of actions to be ran")
    parsed = parser.parse_args()

    todo = {}
    for action in parsed.actions:
        if "=" in action:
            a, v = action.split("=")
            if a == "atempo":
                v = tuple(float(t) for t in v.split(",")) if "," in v else (v, FRAME_RATE)
            todo[a] = v
        else:
            todo[action] = None

    return parsed, todo


if __name__ == "__main__":
    args, actions = _parse_arguments()
    logger.info(f"{os.path.basename(__file__)}:: args -> {args.__dict__}")
    logger.info(f"{json.dumps(actions, indent=4, skipkeys=True, ensure_ascii=False)}")

    if any(k not in COMMAND_ORDER for k in actions.keys()):
        raise Exception(f"invalid command={next(k not in COMMANDS.keys() for k in actions.keys())}")

    main(args.path, actions)
