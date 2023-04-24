import argparse
import logging
import sys
import os
import re
import subprocess
from pathlib import Path

from _utils import inout

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))

PROBE_COMMAND = 'ffprobe -v error -select_streams a:{track} -show_entries stream=codec_name -of default=nokey=1:noprint_wrappers=1 {input}'
COMMAND = 'ffmpeg -i {input} -map 0:a:{track} -c copy {output}.{extension}'

def _parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('path', help='path to be handled')
    parser.add_argument('--track', type=int, default=1, help='track to extract. int (default=1)')
    parser.add_argument('--extension', type=str, default=None, help='extracted track format. str (default=aac)')
    return parser.parse_args()


def _audio_format(path: str, track: int) -> str:
    probe_command = PROBE_COMMAND.format(
        input=path,
        track=track, 
    )
    return re.sub(r"\s", "", subprocess.check_output(probe_command, shell=True).decode("utf-8"), flags=re.UNICODE)


if __name__ == '__main__':
    args = _parse_arguments()
    logger.info(f'{os.path.basename(__file__)}:: args -> {args.__dict__}')

    path = Path(args.path)
    input, output = inout(path)
    extension = args.extension or _audio_format(input, args.track - 1)

    command = COMMAND.format(
        input=input,
        output=output,
        track=args.track - 1, 
        extension=extension,
    )

    logger.info(command)
    output = subprocess.check_output(command, shell=True)

