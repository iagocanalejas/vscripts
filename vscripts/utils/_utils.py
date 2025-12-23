import logging
import subprocess
from pathlib import Path
from typing import Literal

import vscripts.constants as C
from vscripts.constants import HDR_COLOR_TRANSFERS

logger = logging.getLogger("vscripts")


SRT_FFMPEG_CODECS = {"mov_text", "subrip"}
FFMPEG_BASE_COMMAND = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
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


def run_ffmpeg_command(command: list[str]) -> None:
    full_command = FFMPEG_BASE_COMMAND + command
    logger.debug(full_command)
    capture = C.LOG_LEVEL != logging.DEBUG
    subprocess.run(full_command, capture_output=capture, text=True, check=True)


def run_ffprobe_command(path: Path, command: list[str]) -> str:
    full_command = FFPROBE_BASE_COMMAND + command + [str(path)]
    logger.debug(full_command)
    result = subprocess.run(full_command, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def run_handbrake_command(input_path: Path, output_path: Path, command: list[str]) -> None:
    full_command = HANDBRAKE_BASE_COMMAND + ["-i", str(input_path), "-o", str(output_path)] + command
    logger.debug(full_command)
    capture = C.LOG_LEVEL != logging.DEBUG
    subprocess.run(full_command, capture_output=capture, text=True, check=True)


def suffix_by_codec(codec: str | None, codec_type: Literal["audio", "subtitle"]) -> str:
    if not codec:
        return "m4a" if codec_type == "audio" else "srt"
    if codec.lower() in SRT_FFMPEG_CODECS:
        return "srt"
    if codec.lower() in {"ac3", "vorbis"}:
        return "mka"
    return codec.lower()


_CONTAINER_SUBTITLE_SUPPORT = {
    ".mp4": {"mov_text"},
    ".mkv": {"ass", "pgs"},
    ".webm": {"webvtt"},
    ".avi": {"subrip", "srt"},
    ".mov": {"mov_text"},
    ".ogv": {"theora", "subrip"},
}
_EXTENSION_TO_CODEC = {
    ".srt": "subrip",
    ".ass": "ass",
    ".ssa": "ssa",
    ".vtt": "webvtt",
    ".sub": "dvdsub",
    ".idx": "dvdsub",
}


def ffmpeg_subtitle_codec_for_suffix(input: Path, output: Path, codec: str) -> str:
    """
    Returns:
      - 'copy' if -c:s copy is safe
      - subtitle codec name if transcoding is required (e.g. 'srt')
    """
    in_ext = input.suffix.lower()
    out_ext = output.suffix.lower()

    # we can't copy from a subtitle file, must transcode
    if in_ext in {".srt", ".ass", ".ssa", ".vtt", ".sub", ".idx"}:
        if out_ext in {".mp4", ".mov"}:
            return "mov_text"
        if out_ext == ".webm":
            return "webvtt"
        return "subrip"

    # check if the codec is supported in the output container
    supported_codecs = _CONTAINER_SUBTITLE_SUPPORT.get(out_ext, set())
    if codec in supported_codecs:
        return "copy"

    # check if we can infer a suitable codec from the output file extension
    codec_from_suffix = _EXTENSION_TO_CODEC.get(input.suffix.lower())
    if codec_from_suffix and codec_from_suffix in supported_codecs:
        return codec_from_suffix

    return {
        ".mp4": "mov_text",
        ".mkv": "subrip",
        ".webm": "webvtt",
        ".avi": "subrip",
        ".mov": "mov_text",
    }.get(out_ext, "subrip")


_CONTAINER_AUDIO_SUPPORT = {
    ".mp4": {"aac", "mp3", "alac", "ac3", "eac3"},
    ".mov": {"aac", "mp3", "alac", "ac3", "eac3"},
    ".mkv": {"aac", "mp3", "opus", "flac", "vorbis", "ac3", "eac3", "dts", "truehd"},
    ".webm": {"opus", "vorbis"},
}


def ffmpeg_audio_codec_for_suffix(input: Path, output: Path, codec: str) -> str:
    """
    Returns:
      - 'copy' if -c:a copy is safe
      - audio codec name if transcoding is required (e.g. 'aac')
    """
    out_ext = output.suffix.lower()

    supported_codecs = _CONTAINER_AUDIO_SUPPORT.get(out_ext, set())
    if codec in supported_codecs:
        return "copy"

    if out_ext in {".aac", ".wav", ".flac", ".opus"}:
        return codec if out_ext.lstrip(".") == codec else out_ext.lstrip(".")

    if out_ext == ".webm":
        return "opus"
    if out_ext in {".mp4", ".mov"}:
        return "aac"
    return "aac"


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
