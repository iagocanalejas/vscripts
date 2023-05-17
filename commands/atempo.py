import argparse
import logging
import os
import subprocess
from pathlib import Path

from commands._utils import inout

FRAME_RATE = 23.976024


def _parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('path', help='path to be handled')
    parser.add_argument('--rate', type=float, default=25.0,
                        help='framerate from witch we are converting. float (default=25.0)')
    return parser.parse_args()


def atempo(path: str, rate: float = 25.0):
    path = Path(path)
    file, output = inout(path)
    conversion = round(FRAME_RATE / float(rate), 8)

    command = f'ffmpeg -i {file} -filter:a "atempo={conversion}" -vn {output}_out{path.suffix}'
    logging.info(command)

    # noinspection SubprocessShellMode
    subprocess.check_output(command, shell=True)


if __name__ == '__main__':
    args = _parse_arguments()
    logging.info(f'{os.path.basename(__file__)}:: args -> {args.__dict__}')

    atempo(args.path, args.rate)
