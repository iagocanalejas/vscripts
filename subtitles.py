import argparse
import logging
import os
from pathlib import Path
import sys
from typing import List, Optional, Tuple

from commands import append_subs

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))

def _parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('path', help='path to be handled')
    return parser.parse_args()

def _find_subs(root_path: str, file: str) -> Optional[str]:
    path = Path(file)

    # find in current folder
    for i in os.listdir(root_path):
        maybe_match = os.path.join(root_path, i)
        if os.path.isfile(maybe_match) and path.stem in i:
            return maybe_match

    subs_folder = os.path.join(root_path, 'subs')
    for i in os.listdir(subs_folder):
        maybe_match = os.path.join(subs_folder, i)
        if os.path.isfile(maybe_match) and path.stem in i:
            return maybe_match

    return None

if __name__ == '__main__':
    args = _parse_arguments()
    logger.info(f'{os.path.basename(__file__)}:: args -> {args.__dict__}')

    sub_pairs: List[Tuple[str, Optional[str]]] = []
    for i in os.listdir(args.path):
        maybe_file = os.path.join(args.path, i)
        if os.path.isfile(maybe_file):
            sub_pairs.append((maybe_file, _find_subs(args.path, maybe_file)))

    for file, sub_file in sub_pairs:
        if not sub_file:
            logger.error(f'not found subtitles for {file=}')
            continue

        logger.info(f'appending {sub_file=} to {file=}')
        append_subs(file, sub_file)
