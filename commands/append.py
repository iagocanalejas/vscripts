import argparse
import logging
import os
import subprocess
from pathlib import Path

from commands._utils import inout


def _parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('path', help='path to be handled')
    parser.add_argument('--file', type=str, help='file to append')
    return parser.parse_args()


def append(path: str, file: str) -> str:
    path = Path(path)
    target_file, output = inout(path)
    output = f'{output}_out{path.suffix}'

    if not os.path.isfile(file):
        raise ValueError(f'invalid {file=}')

    command = f'ffmpeg -i {target_file} -i {file} -map 0 -map 1 -c copy {output}'
    logging.info(command)

    # noinspection SubprocessShellMode
    subprocess.check_output(command, shell=True)
    return output


if __name__ == '__main__':
    args = _parse_arguments()
    logging.info(f'{os.path.basename(__file__)}:: args -> {args.__dict__}')

    append(args.path, args.file)
