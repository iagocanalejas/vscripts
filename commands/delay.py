import argparse
import logging
import os
import subprocess
from pathlib import Path

from commands._utils import inout


def _parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('path', help='path to be handled')
    parser.add_argument('--delay', type=float, default=1.0, help='delay to apply. float (default=1)')
    return parser.parse_args()


def delay(path: str, delay: float = 1.0) -> str:
    path = Path(path)
    delay = float(delay)
    file, output = inout(path)
    output = f'{output}_delayed_{int(delay)}{path.suffix}'

    command = f'ffmpeg -i {file} -af "adelay={int(delay * 1000)}:all=true" {output}'
    logging.info(command)

    # noinspection SubprocessShellMode
    subprocess.check_output(command, shell=True)
    return output


if __name__ == '__main__':
    args = _parse_arguments()
    logging.info(f'{os.path.basename(__file__)}:: args -> {args.__dict__}')

    delay(args.path, args.delay)
