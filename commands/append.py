import argparse
import logging
import os
import shlex
import subprocess
from pathlib import Path

from commands._utils import inout


def _parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('path', help='path to be handled')
    parser.add_argument('--file', type=str, help='file to append')
    return parser.parse_args()


def append(path: str, file: str) -> str:
    ppath = Path(path)
    input_file, output = inout(ppath)
    output = f'{output}_out{ppath.suffix}'

    if not os.path.isfile(file):
        raise ValueError(f'invalid {file=}')

    extra_file = shlex.quote(file)
    command = f'ffmpeg -i {input_file} -i {extra_file} -map 0 -map 1 -c copy {output}'
    logging.info(command)

    # noinspection SubprocessShellMode
    subprocess.check_output(command, shell=True)
    return output

def append_subs(path: str, file: str) -> str:
    ppath = Path(path)
    input_file, output = inout(ppath)
    output = f'{output}_subs.mkv'
    subtitles_format = file.split('.')[-1].lower()

    if not os.path.isfile(file):
        raise ValueError(f'invalid {file=}')
    if subtitles_format not in ['ass', 'srt', 'ssa']:
        raise ValueError(f'invalid {subtitles_format=}')

    subtitles_file = shlex.quote(file)
    command = f"ffmpeg -i {input_file} -f {subtitles_format} -i {subtitles_file} " \
            + f"-map 0:0 -map 0:1 -map 0:2 -map 1:0 -c:v copy -c:a copy -c:s {subtitles_format} " \
            + f"-metadata:s:s:1 language=spa -disposition:s:1 default {output}"
    logging.info(command)

    # noinspection SubprocessShellMode
    subprocess.check_output(command, shell=True)
    return output



if __name__ == '__main__':
    args = _parse_arguments()
    logging.info(f'{os.path.basename(__file__)}:: args -> {args.__dict__}')

    append(args.path, args.file)
