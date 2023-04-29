import argparse
import logging
import sys
import os
import subprocess
from pathlib import Path

from _utils import inout

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


if __name__ == '__main__':
    args = _parse_arguments()
    logger.info(f'{os.path.basename(__file__)}:: args -> {args.__dict__}')

    path = Path(args.path)
    input, output = inout(path)

    command = COMMAND.format(
        input=input,
        output=output,
        hasten=args.hasten,
        extension=path.suffix,
    )

    logger.info(command)
    output = subprocess.check_output(command, shell=True)
