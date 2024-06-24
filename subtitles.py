#!/usr/bin/env python3

import argparse
import logging
import os
import sys
from pathlib import Path

from vscripts.commands import append_subs

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))


def main(directory_path: str, lang: str):
    sub_pairs: list[tuple[str, str | None]] = []

    # file_by_file processing
    for file in [f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))]:
        file_name, extension = os.path.splitext(file)
        if extension in [".mkv", ".mp4"]:
            sub_pairs.append((os.path.join(directory_path, file), _match_subs(directory_path, file_name)))

    # append found subtitles
    for file, sub_file in sub_pairs:
        if not sub_file:
            logger.error(f"not found subtitles for {file=}")
            continue

        logger.info(f"appending {sub_file=} to {file=}")
        append_subs(Path(sub_file), into=Path(file), lang=lang)


def _match_subs(directory: str, file_name: str, is_subs=False) -> str | None:
    """
    Search for matching subtitle files in a directory.

    This function iterates through the files in the specified directory, checks if they have
    valid subtitle extensions (.ass, .srt, .ssa), and if they contain the specified file name.

    Args:
        directory (str): The directory path to search for subtitle files.
        file_name (str): The file name to match within subtitle file names.

    Returns:
        Optional[str]: The full path to the matching subtitle file, or None if no match is found.
    """
    if not os.path.exists(directory):
        return None

    for file in [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]:
        _, extension = os.path.splitext(file)
        if extension in [".ass", ".srt", ".ssa", ".mks"] and file_name in file:
            return os.path.join(directory, file)

    if is_subs:
        return None

    subs_folder = os.path.join(directory, "subs")
    return _match_subs(subs_folder, file_name, is_subs=True)


def _parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="path to be handled")
    parser.add_argument("-l", "--lang", type=str, default="spa", help="subtitles language")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_arguments()
    logger.info(f"{os.path.basename(__file__)}:: args -> {args.__dict__}")

    main(args.path, args.lang)
