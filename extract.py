import argparse
import logging
import sys
import os
import subprocess
from pathlib import Path

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))

COMMAND = 'ffmpeg -i {path} -map 0:a:{track} -c copy {output}.{extension}'

def _parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('path', help='path to be handled')
    parser.add_argument('--track', type=int, default=1, help='track to extract. int (default=1)')
    parser.add_argument('--extension', type=str, default='aac', help='extracted track format. str (default=aac)')
    return parser.parse_args()


if __name__ == '__main__':
    args = _parse_arguments()
    logger.info(f'{os.path.basename(__file__)}:: args -> {args.__dict__}')

    path = Path(args.path)
    command = COMMAND.format(
        path=path.resolve(strict=True), 
        track=args.track - 1, 
        output=os.path.join(path.parent.resolve(strict=True), path.stem),
        extension=args.extension,
    )
    logger.info(command)

    output = subprocess.check_output(command, shell=True)

