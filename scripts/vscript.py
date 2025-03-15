#!/usr/bin/env python3

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

sys.path[0] = os.path.join(os.path.dirname(__file__), "..")
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))


def main(path_name: str, actions: dict[str, Any], queue: list[str]):
    path = Path(path_name).absolute()
    og_file = Path(path_name).absolute()
    intermediate_files: list[Path] = []
    assert path.is_file()

    for command in queue:
        intermediate_files.append(path)

        fn = COMMANDS[command]
        arg = actions[command]

        if command == COMMAND_APPEND and arg is None:
            # condition when we append a file at the end of a command queue
            path = fn(path, into=og_file)  # pyright: ignore
            continue
        if arg is not None:
            path = fn(path, arg)
            continue
        path = fn(path)  # pyright: ignore

    for f in intermediate_files:
        if f != og_file:
            f.unlink()


def _parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="path to be handled")
    parser.add_argument("actions", type=str, nargs="*", help="list of actions to be ran")
    parsed = parser.parse_args()

    todo: dict[str, Any] = {}
    order: list[str] = []
    for action in parsed.actions:
        if "=" in action:
            a, v = action.split("=")
            if a == COMMAND_ATEMPO:
                v = tuple(float(t) for t in v.split(",")) if "," in v else (v, NTSC_RATE)
            todo[a] = v
            order.append(a)
        else:
            todo[action] = None
            order.append(action)

    return parsed, todo, order


if __name__ == "__main__":
    from vscripts import COMMAND_APPEND, COMMAND_ATEMPO, COMMANDS, NTSC_RATE

    args, actions, queue = _parse_arguments()
    logger.info(f"{os.path.basename(__file__)}:: args -> {args.__dict__}")
    logger.info(f"{json.dumps(actions, indent=4, skipkeys=True, ensure_ascii=False)}")

    if any(k not in COMMANDS.keys() for k in actions.keys()):
        raise Exception(f"invalid command={next(k not in COMMANDS.keys() for k in actions.keys())}")
    # TODO: validate queue is sorted

    main(args.path, actions, queue)
