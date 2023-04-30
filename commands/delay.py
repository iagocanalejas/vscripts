import argparse
import logging
import os
import subprocess
from pathlib import Path

from commands._utils import inout

COMMAND = 'ffmpeg -i {input} -af "adelay={delay}:all=true" {output}_delayed_{delay}{extension}'


def _parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('path', help='path to be handled')
    parser.add_argument('--delay', type=float, default=1.0,
                        help='delay to apply. float (default=1)')
    return parser.parse_args()


def delay(path: str, delay: float = 1.0):
    path = Path(path)
    input, output = inout(path)

    command = COMMAND.format(
        input=input,
        output=output,
        delay=int(delay * 1000),
        extension=path.suffix,
    )

    logging.info(command)
    subprocess.check_output(command, shell=True)


if __name__ == '__main__':
    args = _parse_arguments()
    logging.info(f'{os.path.basename(__file__)}:: args -> {args.__dict__}')

    delay(
        path=args.path,
        delay=args.delay,
    )
