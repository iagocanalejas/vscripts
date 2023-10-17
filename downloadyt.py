#!/usr/bin/env python3

import argparse
import asyncio
import logging
import os
import re
import sys
import time
from typing import List, Optional

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))

_QUEUE: List[str] = []
_PROCESSING: Optional[str] = None
_COMPLETED: List[str] = []
_LAST_MODIFIED: Optional[float] = None

url_validator = re.compile(
    r"^(?:http|ftp)s?://"  # http:// or https://
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain...
    r"localhost|"  # localhost...
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
    r"(?::\d+)?"  # optional port
    r"(?:/?|[/?]\S+)$",
    re.IGNORECASE,
)


def main(file_path: str, output_folder: str):
    global _PROCESSING, _QUEUE, _COMPLETED, _LAST_MODIFIED
    _check_file_changes(file_path)

    try:
        while True:
            if not _PROCESSING and len(_QUEUE) == 0:
                logger.info("nothing to process")

            if _PROCESSING is None and len(_QUEUE) > 0:
                # start processing new element
                asyncio.run(download_to(_QUEUE.pop(0), output_folder))

            _check_file_changes(file_path)
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        _remove_completed_urls(file_path)


async def download_to(url: str, output_folder: str):
    global _PROCESSING, _COMPLETED
    logger.info(f"processing {url=}")
    _PROCESSING = url

    command = ["yt-dlp", "--prefer-ffmpeg", _PROCESSING, "-P", output_folder]

    process = await asyncio.create_subprocess_exec(
        *command,
        limit=1024 * 2048,  # allows to download 2GB files
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    while True:
        line = await process.stdout.readline() if process.stdout else None
        if not line:
            break
        logger.info(line.decode().strip())

    await process.wait()

    _COMPLETED.append(_PROCESSING)
    _PROCESSING = None


def _check_file_changes(file_path: str):
    global _LAST_MODIFIED

    modified = os.path.getmtime(file_path)
    if modified != _LAST_MODIFIED:
        _LAST_MODIFIED = modified
        _add_new_urls(file_path)


def _add_new_urls(file_path: str):
    """Filter lines in a file to check for new URLs to download."""
    with open(file_path) as file:
        lines = file.readlines()

    for pos, line in enumerate(lines):
        line = re.sub(r"\s", "", line)
        if not line or not url_validator.search(line):
            logger.error(f"invalid {pos}: {line=}")
            continue

        if line in _COMPLETED or line in _QUEUE:
            continue

        logger.info(f"adding new {line=}")
        _QUEUE.append(line)


def _remove_completed_urls(file_path: str):
    """Filter lines in a file to remove those already completed."""
    with open(file_path) as file:
        lines = file.readlines()

    with open(file_path, "w") as file:
        for line in lines:
            if re.sub(r"\s", "", line) in _COMPLETED:
                continue
            file.write(line)

    logger.info("\n\nProcessed: ")
    logger.info(_COMPLETED)


def _parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", type=str, default="todo.txt", help="file to watch")
    parser.add_argument("-o", "--out", type=str, default="./out", help="output path")
    parsed = parser.parse_args()
    return parsed


if __name__ == "__main__":
    args = _parse_arguments()
    logger.info(f"{os.path.basename(__file__)}:: args -> {args.__dict__}")

    if not os.path.isfile(args.file):
        raise ValueError(f"{args.file=} is not a file")
    if not os.path.isdir(args.out):
        raise ValueError(f"{args.out=} is not a directory")

    main(args.file, args.out)
