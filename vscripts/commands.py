import logging
import os
import subprocess
from pathlib import Path

from .constants import NTSC_RATE, PAL_RATE
from .streams import AudioStream, SubtitleStream


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

    command = ["ffmpeg", "-i", str(into), "-i", str(file), "-map", "0", "-map", "1", "-c", "copy", str(output_path)]
    logging.info(command)

    subprocess.run(command, text=True)
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

    command = [
        "ffmpeg",
        "-i",
        str(into),
        "-i",
        str(subs_file),
        "-map",
        "0",
        "-map",
        "1",
        "-c",
        "copy",
        f"-metadata:s:s:{len(SubtitleStream.from_file(str(into)))}",
        f"language={lang}",
        "-scodec",
        "mov_text" if "mp4" in file_extension else "",
        str(output_path),
    ]
    logging.info(command)

    subprocess.run(command, text=True)
    return output_path


def atempo(file: Path, rates: tuple[float, float] = (PAL_RATE, NTSC_RATE)) -> Path:
    """
    Change the playback speed of an audio or video file using FFmpeg and save the result as a new file.

    Args:
        target (Path): The path to the audio or video file to be processed.
        rate (tuple[float, float], optional): The conversion rates in the format (from_rate, to_rate).

    Returns: The path to the newly created file with the adjusted playback speed.
    """
    return atempo_with(file, round(float(rates[1]) / float(rates[0]), 8))


def atempo_with(file: Path, value: float) -> Path:
    """
    Change the playback speed of an audio or video file using FFmpeg and save the result as a new file.

    Args:
        target (Path): The path to the audio or video file to be processed.
        value (float): The conversion rate.

    Returns: The path to the newly created file with the adjusted playback speed.
    """
    workspace, file_name, file_extension = file.parent, file.stem, file.suffix
    output_path = workspace.joinpath(f"{file_name}_atempo_{value}{file_extension}")

    command = ["ffmpeg", "-i", str(file), "-filter:a", f"atempo={value}", "-vn", str(output_path)]
    logging.info(command)

    subprocess.run(command, text=True)
    return output_path


def atempo_video(file: Path, rate: float = NTSC_RATE) -> Path:
    """
    Change the playback speed of a video file using FFmpeg and save the result as a new file.

    Args:
        file (Path): The path to the video file to be processed.
        rate (float, optional): The conversion rate.

    Returns: The path to the newly created file with the adjusted playback speed.
    """
    workspace, file_name, file_extension = file.parent, file.stem, file.suffix
    output_path = workspace.joinpath(f"{file_name}_atempo-video{file_extension}")

    command = ["ffmpeg", "-i", str(file), "-r", f"{rate}", "-an", "-sn", str(output_path)]
    logging.info(command)

    subprocess.run(command, text=True)
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

    command = ["ffmpeg", "-i", str(file), "-af", f"adelay={int(float(delay) * 1000)}:all=true", str(output_path)]
    logging.info(command)

    subprocess.run(command, text=True)
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
    audio_stream = AudioStream.from_file_stream(str(file), track)
    audio_language = audio_stream.tags.get("language", "unk")
    output_path = workspace.joinpath(f"{file_name}_{audio_language}.{audio_stream.codec_name}")

    if os.path.isfile(output_path):
        logging.debug(f"skipping {output_path=} as it already exists")
        return output_path

    command = ["ffmpeg", "-i", str(file), "-map", f"0:a:{track}", "-c", "copy", str(output_path)]
    logging.info(command)

    subprocess.run(command, text=True)
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

    command = ["ffmpeg", "-i", str(file), "-ss", f"{hasten}", "-acodec", "copy", str(output_path)]
    logging.info(command)

    subprocess.run(command, text=True)
    return output_path


def reencode(file: Path, output: Path, quality: str) -> Path:
    """
    Re-encode a multimedia file using HandBrakeCLI and save the result as a new file.

    Args:
        file (Path): The path to the multimedia file to re-encode.
        output (Path): The path to save the re-encoded multimedia file.
        quality (str): The quality preset to use for re-encoding.

    Returns: The path to the newly created re-encoded multimedia file.
    """

    command = [
        "HandBrakeCLI",
        f"--preset={quality}",
        "-i",
        str(file),
        "-o",
        str(output),
        "--format=mkv",
        "--all-audio",
        "--audio-copy-mask=ac3,dts,dtshd,eac3,truehd",
        "--audio-fallback=ac3",
        "--all-subtitles",
        "--subtitle-burn=none",
    ]
    logging.info(command)
    subprocess.run(command, text=True)
    return output
