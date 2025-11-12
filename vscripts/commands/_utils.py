import logging
import os
import subprocess
from pathlib import Path
from typing import Literal

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


def run_ffmpeg_command(command: list[str]) -> None:
    quiet = os.getenv("TEST_ENV", "false").lower() == "true"
    if quiet:
        subprocess.run(command, text=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.run(command, text=True, check=True)


def get_file_duration(path: Path) -> float:
    return float(
        subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(path),
            ]
        ).strip()
    )


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
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            stream_map[stream_type],
            "-show_entries",
            "stream=index",
            "-of",
            "csv=p=0",
            str(path),
        ],
        capture_output=True,
        text=True,
    )
    return bool(result.stdout.strip())
