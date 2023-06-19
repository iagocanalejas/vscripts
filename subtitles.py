import argparse
import logging
import os
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

def _match_subs(root: str, file_path: str) -> Optional[str]:
    file_name = os.path.basename(file_path)

    # find in current folder
    for i in os.listdir(root):
        maybe_match = os.path.join(root, i)
        _, extension = os.path.splitext(maybe_match)
        if os.path.isfile(maybe_match) \
                and extension in ['.ass', '.srt', '.ssa'] \
                and file_name in i:
            return maybe_match

    # find in 'subs' folder
    subs_folder = os.path.join(root, 'subs')
    if not os.path.exists(subs_folder):
        return None

    for i in os.listdir(subs_folder):
        maybe_match = os.path.join(subs_folder, i)
        print(maybe_match, file_name)
        if os.path.isfile(maybe_match) \
                and file_name in i:
            return maybe_match

    return None

if __name__ == '__main__':
    args = _parse_arguments()
    logger.info(f'{os.path.basename(__file__)}:: args -> {args.__dict__}')

    sub_pairs: List[Tuple[str, Optional[str]]] = []
    for i in os.listdir(args.path):
        maybe_file = os.path.join(args.path, i)
        file_name, extension = os.path.splitext(maybe_file)
        if os.path.isfile(maybe_file) \
                and extension in ['.mkv', '.mp4']:
            sub_pairs.append((maybe_file, _match_subs(args.path, file_name)))

    for file, sub_file in sub_pairs:
        if not sub_file:
            logger.error(f'not found subtitles for {file=}')
            continue

        logger.info(f'appending {sub_file=} to {file=}')
        append_subs(file, sub_file)
