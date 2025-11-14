import logging
import os
import subprocess
from pathlib import Path
from typing import Literal

from vscripts.constants import HDR_COLOR_TRANSFERS

logger = logging.getLogger("vscripts")


def get_output_file_path(maybe_output: Path, default_name: str) -> Path:
    if maybe_output.is_dir():
        if not maybe_output.exists():
            maybe_output.mkdir(parents=True, exist_ok=True)
        maybe_output = maybe_output / default_name
    return maybe_output


def ffmpeg_copy_by_codec(codec: str | None) -> list[str]:
    if codec and codec.lower() in ["mov_text"]:
        return ["-c:s", "srt"]
    return ["-c", "copy"]


def suffix_by_codec(codec: str | None, codec_type: Literal["audio", "subtitle"]) -> str:
    if not codec:
        return "m4a" if codec_type == "audio" else "srt"
    if codec.lower() == "mov_text":
        return "srt"
    if codec.lower() == "ac3":
        return "mka"
    return codec.lower()


FFMPEG_BASE_COMMAND = ["ffmpeg", "-hide_banner", "-loglevel", "error"]


def run_ffmpeg_command(command: list[str]) -> None:
    quiet = os.getenv("TEST_ENV", "false").lower() == "true"
    full_command = FFMPEG_BASE_COMMAND + command
    logging.debug(full_command)
    if quiet:
        subprocess.run(full_command, text=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.run(full_command, text=True, check=True)


FFPROBE_BASE_COMMAND = ["ffprobe", "-hide_banner", "-loglevel", "error"]


def run_ffprobe_command(path: Path, command: list[str]) -> str:
    full_command = FFPROBE_BASE_COMMAND + command + [str(path)]
    logging.debug(full_command)
    result = subprocess.run(full_command, capture_output=True, text=True, check=True)
    return result.stdout.strip()


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


def run_handbrake_command(input_path: Path, output_path: Path, command: list[str]) -> None:
    quiet = os.getenv("TEST_ENV", "false").lower() == "true"
    full_command = HANDBRAKE_BASE_COMMAND + ["-i", str(input_path), "-o", str(output_path)] + command
    logging.debug(full_command)
    if quiet:
        subprocess.run(full_command, text=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.run(full_command, text=True, check=True)


def get_file_duration(path: Path) -> float:
    command = [
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
    ]
    return float(run_ffprobe_command(path, command))


def has_video(path: Path) -> bool:
    return has_stream(path, "video")


def has_audio(path: Path) -> bool:
    return has_stream(path, "audio")


def has_subtitles(path: Path) -> bool:
    return has_stream(path, "subtitle")


def has_stream(path: Path, stream_type: Literal["audio", "subtitle", "video"]) -> bool:
    stream_map = {"audio": "a", "subtitle": "s", "video": "v"}
    if stream_type not in stream_map:
        raise ValueError(f"Invalid stream type: {stream_type}")
    command = [
        "-select_streams",
        stream_map[stream_type],
        "-show_entries",
        "stream=index",
        "-of",
        "csv=p=0",
    ]
    return bool(run_ffprobe_command(path, command))


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


def to_srt_timestamp(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
