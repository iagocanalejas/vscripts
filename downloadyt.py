import argparse
import asyncio
import logging
import os
import re
import sys
import time
from typing import TextIO, List, Optional

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))

_QUEUE: List[str] = []
_PROCESSING: Optional[str] = None
_COMPLETED: List[str] = []
_LAST_MODIFIED: Optional[float] = None

url_validator = re.compile(
    r'^(?:http|ftp)s?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)


def main(file: str, out: str):
    global _PROCESSING, _QUEUE, _COMPLETED, _LAST_MODIFIED

    _LAST_MODIFIED = os.path.getmtime(file)
    _check_changes(file)

    try:
        while True:
            time.sleep(1)

            if not _PROCESSING and len(_QUEUE) == 0:
                logger.info('nothing to process')

            if _PROCESSING is None and len(_QUEUE) > 0:
                # start processing new element
                _PROCESSING = _QUEUE.pop(0)
                logger.info(f'{_PROCESSING=}')
                asyncio.run(run_subprocess(out))

            _check_changes(file)
    except KeyboardInterrupt:
        pass
    finally:
        _complete(file)


async def run_subprocess(output: str):
    global _PROCESSING, _COMPLETED
    if _PROCESSING is None:
        logger.error(f'received null url')
        raise ValueError

    command = ['yt-dlp', '--prefer-ffmpeg', _PROCESSING, '-P', output]

    process = await asyncio.create_subprocess_exec(
        *command,
        limit=1024 * 2048,  # allows to download 2GB files
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT
    )

    while True:
        line = await process.stdout.readline()
        if not line:
            break
        logger.info(line.decode().strip())

    await process.wait()

    _COMPLETED.append(_PROCESSING)
    _PROCESSING = None


def _check_changes(file: str):
    global _LAST_MODIFIED

    modified = os.path.getmtime(file)
    if modified != _LAST_MODIFIED:
        _LAST_MODIFIED = modified
        with open(file) as freader:
            _process_urls(freader)


def _process_urls(reader: TextIO):
    for line in reader.readlines():
        line = re.sub(r"\s", "", line)
        if not url_validator.search(line):
            if line:
                logger.error(f'invalid {line=}')
            continue

        if line in _COMPLETED or line in _QUEUE:
            continue

        logger.info(f'adding new {line=}')
        _QUEUE.append(line)


def _complete(file: str):
    with open(file, "r") as f:
        lines = f.readlines()
    with open(file, "w") as f:
        for line in lines:
            if re.sub(r"\s", "", line) not in _COMPLETED:
                f.write(line)

    logger.info('\n\nProcessed: ')
    logger.info(_COMPLETED)


def _parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', type=str, default='todo.txt', help='file to watch')
    parser.add_argument('-o', '--out', type=str, default='./out', help='output path')
    parsed = parser.parse_args()
    return parsed


if __name__ == '__main__':
    args = _parse_arguments()
    logger.info(f'{os.path.basename(__file__)}:: args -> {args.__dict__}')

    if not os.path.isfile(args.file):
        raise ValueError(f'{args.file=} is not a file')
    if not os.path.isdir(args.out):
        raise ValueError(f'{args.out=} is not a directory')

    main(args.file, args.out)
