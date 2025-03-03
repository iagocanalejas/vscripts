#!/usr/bin/env python3

import argparse
import logging
import os
import sys
from pathlib import Path

from vscripts import reencode
from vscripts.matcher import NameMatcher

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))

PRESSETS = {
    "1080p": "H.265 NVENC 1080p",
    "2160p": "H.265 NVENC 2160p 4K",
    "AV1": "AV1 QSV 2160p 4K",
}


def main(files: list[str], quality: str):
    total_files = len(files)
    for i, f in enumerate(files):
        path, file_name = os.path.dirname(f), os.path.basename(f)
        cleaned_file_name = Path(os.path.join(path, NameMatcher(file_name).clean()))
        logger.info(f"{i + 1}/{total_files} reencoding {file_name} -> {cleaned_file_name}")
        reencode(Path(f).absolute(), cleaned_file_name.absolute(), quality)


def _parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("folder_or_path", help="path to be handled")
    parser.add_argument("-q", "--quality", type=str, default="1080p", help="quality of the output [1080p, 2160p]")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_arguments()
    logger.info(f"{os.path.basename(__file__)}:: args -> {args.__dict__}")

    assert args.quality in PRESSETS, f"invalid quality: {args.quality}"
    assert os.path.exists(args.folder_or_path), f"invalid path: {args.folder_or_path}"

    files = (
        [os.path.join(args.folder_or_path, f) for f in os.listdir(args.folder_or_path)]
        if os.path.isdir(args.folder_or_path)
        else [os.path.abspath(args.folder_or_path)]
    )
    files = [f for f in files if f.lower().endswith((".mkv", ".mp4", ".avi"))]

    assert len(files) > 0, f"no valid files found in {args.folder_or_path}"

    main(files, PRESSETS[args.quality])
