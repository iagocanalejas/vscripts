import logging
import os
import subprocess
from pathlib import Path
from typing import Literal

from vscripts.constants import HDR_COLOR_TRANSFERS

logger = logging.getLogger("vscripts")


SRT_FFMPEG_CODECS = {"mov_text", "subrip"}
FFMPEG_BASE_COMMAND = ["ffmpeg", "-hide_banner", "-loglevel", "error"]
FFPROBE_BASE_COMMAND = ["ffprobe", "-hide_banner", "-loglevel", "error"]
HANDBRAKE_BASE_COMMAND = [
    "HandBrakeCLI",
    "--verbose=3",
    "--format=mkv",
    "--all-audio",
    "--audio-copy-mask=ac3,dts,dtshd,eac3,truehd",
    "--audio-fallback=ac3",
    "--all-subtitles",
    "--subtitle-burn=none",
]
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".hevc", ".h264"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".aac", ".ogg", ".eac3", ".ac3", ".m4a", ".mka"}
SUBTITLE_EXTENSIONS = {".srt", ".vtt", ".ass", ".ssa"}


def get_output_file_path(maybe_output: Path, default_name: str) -> Path:
    """
    Determine the output file path based on the provided maybe_output path.
    If maybe_output is a directory, create it if it doesn't exist and append the default_name to it.
    Args:
        maybe_output (Path): The potential output path, which can be a file or directory.
        default_name (str): The default file name to use if maybe_output is a directory.
    Returns: The resolved output file path.
    """
    if maybe_output.is_dir():
        if not maybe_output.exists():
            maybe_output.mkdir(parents=True, exist_ok=True)
        maybe_output = maybe_output / default_name
    return maybe_output


def suffix_by_codec(codec: str | None, codec_type: Literal["audio", "subtitle"]) -> str:
    if not codec:
        return "m4a" if codec_type == "audio" else "srt"
    if codec.lower() in SRT_FFMPEG_CODECS:
        return "srt"
    if codec.lower() == "ac3":
        return "mka"
    return codec.lower()


def run_ffmpeg_command(command: list[str]) -> None:
    quiet = os.getenv("TEST_ENV", "false").lower() == "true"
    full_command = FFMPEG_BASE_COMMAND + command
    logging.debug(full_command)
    if quiet:
        subprocess.run(full_command, text=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.run(full_command, text=True, check=True)


def run_ffprobe_command(path: Path, command: list[str]) -> str:
    full_command = FFPROBE_BASE_COMMAND + command + [str(path)]
    logging.debug(full_command)
    result = subprocess.run(full_command, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def run_handbrake_command(input_path: Path, output_path: Path, command: list[str]) -> None:
    quiet = os.getenv("TEST_ENV", "false").lower() == "true"
    full_command = HANDBRAKE_BASE_COMMAND + ["-i", str(input_path), "-o", str(output_path)] + command
    logging.debug(full_command)
    if quiet:
        subprocess.run(full_command, text=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.run(full_command, text=True, check=True)


def is_hdr(path: Path) -> bool:
    command = [
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=color_transfer,color_primaries,color_space",
        "-of",
        "default=nw=1:nk=1",
    ]
    result = run_ffprobe_command(path, command)
    return any(h in result.lower() for h in HDR_COLOR_TRANSFERS)


def is_subs(path: Path) -> bool:
    return path.suffix.lower() in SUBTITLE_EXTENSIONS


def is_audio(path: Path) -> bool:
    return path.suffix.lower() in AUDIO_EXTENSIONS


def is_video(path: Path) -> bool:
    return path.suffix.lower() in VIDEO_EXTENSIONS


def infer_media_type(path: Path) -> Literal["video", "audio", "subtitle", "unknown"]:
    ext = path.suffix.lower()
    if ext in VIDEO_EXTENSIONS:
        return "video"
    if ext in AUDIO_EXTENSIONS:
        return "audio"
    if ext in SUBTITLE_EXTENSIONS:
        return "subtitle"
    return "unknown"
