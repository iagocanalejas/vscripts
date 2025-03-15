#!/usr/bin/env python3

import argparse
import logging
import os
import sys
import time

sys.path[0] = os.path.join(os.path.dirname(__file__), "..")
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))


def main(todo_file: str, output_folder: str):
    work_queue = WorkQueue(todo_file)

    empty_count = 0
    try:
        while True:
            work_queue.check_file_changes()

            if not work_queue.can_process:
                logger.info("nothing to process")
                empty_count += 1
                if empty_count > 10:
                    break

            work = work_queue.next()
            if work:
                empty_count = 0
                logger.info(f"processing {work=}")
                if "{}" in work:
                    chunk_download(work, output_folder, f"download_{work_queue.completed}")
                else:
                    yt_download(work, output_folder)

            time.sleep(1)
    finally:
        work_queue.remove_completed_urls()


def _parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", type=str, default="todo.txt", help="file to watch")
    parser.add_argument("-o", "--out", type=str, default="./out", help="output path")
    parsed = parser.parse_args()
    return parsed


if __name__ == "__main__":
    from vscripts.downloader import WorkQueue, chunk_download, yt_download

    args = _parse_arguments()
    logger.info(f"{os.path.basename(__file__)}:: args -> {args.__dict__}")

    if not os.path.isfile(args.file):
        raise ValueError(f"{args.file=} is not a file")
    if not os.path.isdir(args.out):
        raise ValueError(f"{args.out=} is not a directory")

    main(args.file, args.out)
