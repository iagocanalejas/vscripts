import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path

from commands._utils import inout

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))

COMMAND = 'ffmpeg -i {input} -ss {hasten} -acodec copy {output}_hastened_{hasten}{extension}'


def _parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('path', help='path to be handled')
    parser.add_argument('--hasten', type=float, default=1.0,
                        help='hasten to apply. float (default=1.0)')
    return parser.parse_args()


def hasten(path: str, hasten: float = 1.0):
    path = Path(path)
    input, output = inout(path)

    command = COMMAND.format(
        input=input,
        output=output,
        hasten=hasten,
        extension=path.suffix,
    )

    logger.info(command)
    subprocess.check_output(command, shell=True)


if __name__ == '__main__':
    args = _parse_arguments()
    logger.info(f'{os.path.basename(__file__)}:: args -> {args.__dict__}')

    hasten(
        path=args.path,
        hasten=args.hasten,
    )
