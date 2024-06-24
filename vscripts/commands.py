import logging
import os
import shlex
import subprocess
from pathlib import Path

from .constants import ES_RATE, FRAME_RATE
from .utils import retrieve_audio_format, retrieve_number_of_subtitle_tracks


def append(file: Path, into: Path) -> Path:
    """
    Append the contents of one multimedia file into another using FFmpeg and save the result as a new file.

    Args:
        file (Path): The path to the file that will be appended into another.
        into (Path): The path to the destination file into which 'file' will be appended.

    Returns: The path to the newly created file that contains the appended content.
    """
    workspace, file_name, file_extension = into.parent, into.stem, into.suffix
    output_path = workspace.joinpath(f"{file_name}_out{file_extension}")

    if not os.path.isfile(file):
        raise ValueError(f"invalid {file=}")

    input_file = shlex.quote(str(into))
    appended_file = shlex.quote(str(file))
    output_file = shlex.quote(str(output_path))

    command = f"ffmpeg -i {input_file} -i {appended_file} -map 0 -map 1 -c copy {output_file}"
    logging.info(command)

    subprocess.check_output(command, shell=True)
    return output_path


def append_subs(subs_file: Path, into: Path, lang: str = "spa") -> Path:
    """
    Append subtitles to a video file using FFmpeg and save it as a new file.

    Args:
        file (Path): The path to the subtitle file to append.
        into (Path): The path to the input video file.

    Returns: The path to the newly created video file with subtitles.
    """
    workspace, file_name, file_extension = into.parent, into.stem, into.suffix
    output_path = workspace.joinpath(f"{file_name}_subs{'.mkv' if 'mkv' in file_extension else '.mp4'}")

    original_file = shlex.quote(str(into))
    subtitles_file = shlex.quote(str(subs_file))
    output_file = shlex.quote(str(output_path))

    subtitle_tracks = retrieve_number_of_subtitle_tracks(original_file)

    command = (
        f"ffmpeg -i {original_file} -i {subtitles_file} -map 0 -map 1 -c copy"
        + f" -metadata:s:s:{subtitle_tracks} language={lang} {'-scodec mov_text ' if 'mp4' in file_extension else ''}"
        + f" {output_file}"
    )
    logging.info(command)

    subprocess.check_output(command, shell=True)
    return output_path


def atempo(file: Path, rate: tuple[float, float] = (ES_RATE, FRAME_RATE)) -> Path:
    """
    Change the playback speed of an audio or video file using FFmpeg and save the result as a new file.

    Args:
        target (Path): The path to the audio or video file to be processed.
        rate (tuple[float, float], optional): The conversion rates (from, to).

    Returns: The path to the newly created file with the adjusted playback speed.
    """
    workspace, file_name, file_extension = file.parent, file.stem, file.suffix
    output_path = workspace.joinpath(f"{file_name}_atempo{file_extension}")

    input_file = shlex.quote(str(file))
    output_file = shlex.quote(str(output_path))
    conversion = round(rate[1] / float(rate[0]), 8)

    command = f'ffmpeg -i {input_file} -filter:a "atempo={conversion}" -vn {output_file}'
    logging.info(command)

    subprocess.check_output(command, shell=True)
    return output_path


def delay(file: Path, delay: float = 1.0) -> Path:
    """
    Apply an audio delay effect to an audio or video file using FFmpeg and save the result as a new file.

    Args:
        file (Path): The path to the audio or video file to be processed.
        delay (float, optional): The delay time in seconds. Default is 1.0 second.

    Returns: The path to the newly created file with the audio delay effect applied.
    """
    workspace, file_name, file_extension = file.parent, file.stem, file.suffix
    output_path = workspace.joinpath(f"{file_name}_delayed_{delay}{file_extension}")

    input_file = shlex.quote(str(file))
    output_file = shlex.quote(str(output_path))
    delay = int(float(delay) * 1000)

    command = f'ffmpeg -i {input_file} -af "adelay={delay}:all=true" {output_file}'
    logging.info(command)

    subprocess.check_output(command, shell=True)
    return output_path


def extract(file: Path, track: int = 0) -> Path:
    """
    Extract a specific audio track from a video file using FFmpeg and save it as a new audio file.

    Args:
        file (Path): The path to the video file from which to extract the audio track.
        track (int, optional): The index of the audio track to extract. Default is 0.

    Returns: The path to the newly created audio file containing the extracted audio track.
    """
    workspace, file_name = file.parent, file.stem
    output_path = workspace.joinpath(f"{file_name}.{retrieve_audio_format(shlex.quote(str(file)), track)}")

    input_file = shlex.quote(str(file))
    output_file = shlex.quote(str(output_path))

    command = f"ffmpeg -i {input_file} -map 0:a:{track} -c copy {output_file}"
    logging.info(command)

    subprocess.check_output(command, shell=True)
    return output_path


def hasten(file: Path, hasten: float = 1.0) -> Path:
    """
    Adjust the playback speed of an audio or video file using FFmpeg and save it as a new file.

    Args:
        file (Path): The path to the input audio or video file to adjust.
        hasten (float, optional): The hasten factor to adjust playback speed. Default is 1.0 (no change).

    Returns: The path to the newly created hastened audio or video file.
    """
    workspace, file_name, file_extension = file.parent, file.stem, file.suffix
    output_path = workspace.joinpath(f"{file_name}_hastened_{hasten}{file_extension}")

    input_file = shlex.quote(str(file))
    output_file = shlex.quote(str(output_path))

    command = f"ffmpeg -i {input_file} -ss {hasten} -acodec copy {output_file}"
    logging.info(command)

    subprocess.check_output(command, shell=True)
    return output_path
