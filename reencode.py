#!/usr/bin/env python3

import argparse
import logging
import os
import re
import sys
from pathlib import Path

from vscripts import reencode

from pyutils.strings import remove_brackets, remove_trailing_hyphen, whitespaces_clean

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))

PRESSETS = {
    "1080p": "H.265 NVENC 1080p",
    "2160p": "H.265 NVENC 2160p 4K",
    "AV1": "AV1 QSV 2160p 4K",
}


EPISODE_REGEXES = [
    r"[ -]*(\d+)x(\d+)[ -]*",
    r"[ -]*S(\d+)E(\d+)[ -]*",
]


def main(files: list[str], quality: str):
    total_files = len(files)
    for i, f in enumerate(files):
        path, file_name = os.path.dirname(f), os.path.basename(f)
        cleaned_file_name = Path(os.path.join(path, _reencoded_file_name(file_name)))
        logger.info(f"{i + 1}/{total_files} reencoding {file_name} -> {cleaned_file_name}")
        reencode(Path(f).absolute(), cleaned_file_name.absolute(), quality)


def _reencoded_file_name(file_name: str) -> str:
    file_name = remove_brackets(file_name)

    # remove everything after resolution except the extension
    file_name = re.sub(r"_?\d+p.*\.(\w{3})", r".\1", file_name, re.IGNORECASE)

    file_name = file_name.replace("_", " ")
    file_name = file_name.replace(" (1)", "")  # remove ' (1)' for copied files
    file_name = file_name.replace(" (TV)", "")  # remove ' (TV)' for some season names

    # replace episode numbers with S01E01 format
    file_name = re.sub("|".join(EPISODE_REGEXES), r" - S\1E\2 - ", file_name, re.IGNORECASE)
    file_name = whitespaces_clean(remove_trailing_hyphen(file_name))

    return f"{os.path.splitext(file_name)[0]}.mkv"


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
