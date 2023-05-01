import argparse
import logging
import os
import re
import subprocess
from pathlib import Path

from commands._utils import inout, expand_path


def _parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('path', help='path to be handled')
    parser.add_argument('--track', type=int, default=0, help='track to extract. int (default=1)')
    return parser.parse_args()


def _audio_format(path: str, track: int) -> str:
    probe_command = f'ffprobe -v error -select_streams a:{track} -show_entries stream=codec_name -of default=nokey=1:noprint_wrappers=1 {path}'

    # noinspection SubprocessShellMode
    return re.sub(r"\s", "", subprocess.check_output(probe_command, shell=True).decode("utf-8"), flags=re.UNICODE)


def extract(path: str, track: int = 1):
    errors = []
    files = expand_path(path)

    for file in files:
        logging.info(f'{file=}')

        path = Path(file)
        file, output = inout(path)

        command = f'ffmpeg -i {file} -map 0:a:{track} -c copy {output}.{_audio_format(file, track)}'
        logging.info(command)

        try:
            # noinspection SubprocessShellMode
            subprocess.check_output(command, shell=True)
        except subprocess.CalledProcessError as e:
            errors.append((file, e))

    for file, _ in errors:
        logging.error(f'errored {file=}')


if __name__ == '__main__':
    args = _parse_arguments()
    logging.info(f'{os.path.basename(__file__)}:: args -> {args.__dict__}')

    extract(
        path=args.path,
        track=args.track,
    )
