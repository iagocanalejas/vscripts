import argparse
import logging
import os
import subprocess
from pathlib import Path

try:
    from commands._utils import inout
except ImportError:
    from _utils import inout


def _parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('path', help='path to be handled')
    parser.add_argument('--hasten', type=float, default=1.0, help='hasten to apply. float (default=1.0)')
    return parser.parse_args()


def hasten(path: str, hasten: float = 1.0) -> str:
    ppath = Path(path)
    file, output = inout(ppath)
    output = f'{output}_hastened_{hasten}{ppath.suffix}'

    command = f'ffmpeg -i {file} -ss {hasten} -acodec copy {output}'
    logging.info(command)

    # noinspection SubprocessShellMode
    subprocess.check_output(command, shell=True)
    return output


if __name__ == '__main__':
    args = _parse_arguments()
    logging.info(f'{os.path.basename(__file__)}:: args -> {args.__dict__}')

    hasten(args.path, args.hasten)
