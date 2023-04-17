import argparse
import logging
import sys
import os
import subprocess
from pathlib import Path

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))

FRAME_RATE = 23.976024
COMMAND = 'ffmpeg -i {path} -filter:a "atempo={conversion}" -vn {output}_out{extension}'

def _parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('path', help='path to be handled')
    parser.add_argument('--rate', type=float, default=25.0, help='framerate from witch we are converting. float (default=25.0)')
    return parser.parse_args()


if __name__ == '__main__':
    args = _parse_arguments()
    logger.info(f'{os.path.basename(__file__)}:: args -> {args.__dict__}')

    path = Path(args.path)
    conversion = round(FRAME_RATE / args.rate, 8)
    if conversion == 1:
        raise Exception(f'Converting nothing {conversion=}')

    command = COMMAND.format(
        path=path.resolve(strict=True), 
        conversion=conversion, 
        output=os.path.join(path.parent.resolve(strict=True), path.stem), 
        extension=path.suffix,
    )
    logger.info(command)

    output = subprocess.check_output(command, shell=True)

