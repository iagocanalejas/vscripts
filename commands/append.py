import argparse
import logging
import os
import shlex
import subprocess
from pathlib import Path

try:
    from commands._utils import inout
except ImportError:
    from _utils import inout


def _parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('path', help='path to be handled')
    parser.add_argument('--file', type=str, help='file to append')
    return parser.parse_args()


def append(path: str, file: str) -> str:
    ppath = Path(path)
    in_file, out_file = inout(ppath)
    out_file = f'{out_file}_out{ppath.suffix}'

    if not os.path.isfile(file):
        raise ValueError(f'invalid {file=}')

    extra_file = shlex.quote(file)
    command = f'ffmpeg -i {in_file} -i {extra_file} -map 0 -map 1 -c copy {out_file}'
    logging.info(command)

    # noinspection SubprocessShellMode
    subprocess.check_output(command, shell=True)
    return out_file

def append_subs(path: str, file: str) -> str:
    in_file, out_file = inout(Path(path))
    out_file = f'{out_file}_subs.mkv' if '.mkv' in in_file else f'{out_file}_subs.mp4'
    in_subs_format = file.split('.')[-1].lower()
    out_subs_format = in_subs_format if '.mkv' in in_file else 'mov_text'

    if not os.path.isfile(file):
        raise ValueError(f'invalid {file=}')
    if in_subs_format not in ['ass', 'srt', 'ssa']:
        raise ValueError(f'invalid {in_subs_format=}')

    subs_file = shlex.quote(file)
    command = f"ffmpeg -i {in_file} -f {in_subs_format} -i {subs_file} " \
            + f"-map 0:0 -map 0:1 -map 0:2 -map 1:0 -c:v copy -c:a copy -c:s {out_subs_format} " \
            + f"-metadata:s:s:1 language=spa -disposition:s:1 default {out_file}"
    logging.info(command)

    # noinspection SubprocessShellMode
    subprocess.check_output(command, shell=True)
    return out_file



if __name__ == '__main__':
    args = _parse_arguments()
    logging.info(f'{os.path.basename(__file__)}:: args -> {args.__dict__}')

    append(args.path, args.file)
