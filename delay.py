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

COMMAND = 'ffmpeg -i {input} -af "adelay={delay}s:all=true" {output}_delayed{extension}'

def _parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('path', help='path to be handled')
    parser.add_argument('--delay', type=int, default=1, help='delay to apply. float (default=1)')
    return parser.parse_args()


if __name__ == '__main__':
    args = _parse_arguments()
    logger.info(f'{os.path.basename(__file__)}:: args -> {args.__dict__}')

    path = Path(args.path)
    input, output = inout(path)

    command = COMMAND.format(
        input=input,
        output=output,
        delay=args.delay,
        extension=path.suffix,
    )

    logger.info(command)
    output = subprocess.check_output(command, shell=True)

