from pathlib import Path
from typing import Literal

from vscripts.utils import run_ffmpeg_command
from vscripts.utils._utils import run_ffprobe_command


def generate_test_subs(path: Path) -> Path:
    content = """1
00:00:00,000 --> 00:00:00,800
Hello World!

2
00:00:00,900 --> 00:00:01,500
This is a test.
"""
    path.write_text(content, encoding="utf-8")
    return path


def generate_test_audio(path: Path, freq: int = 1000, duration: float = 2.5, streams: int = 1) -> Path:
    command = []

    for _ in range(streams):
        command += ["-f", "lavfi", "-i", f"sine=frequency={freq}:duration={duration}"]

    for i in range(streams):
        command += ["-map", f"{i}:a"]

    command += [
        str(path),
        "-y",
    ]

    run_ffmpeg_command(command)
    return path


def generate_test_video(path: Path, duration: float = 1.0, rate: float = 30.0) -> Path:
    command = [
        "-f",
        "lavfi",
        "-i",
        f"color=c=blue:s=64x64:d={duration}",
        "-c:v",
        "libx264",
        "-r",
        str(rate),
        str(path),
        "-y",
    ]
    run_ffmpeg_command(command)
    return path


def generate_test_full(
    tmp_path: Path,
    duration: float = 1.0,
    rate: float = 30.0,
    output_name: str = "full_video.mp4",
) -> Path:
    video_path = tmp_path / "video.mp4"
    subs_path = tmp_path / "subs.srt"
    audio_path = tmp_path / "audio.mka"
    generate_test_video(video_path, duration=duration, rate=rate)
    generate_test_audio(audio_path, duration=duration)
    generate_test_subs(subs_path)

    output = tmp_path / output_name

    command = [
        "-i",
        str(video_path),
        "-i",
        str(audio_path),
        "-i",
        str(subs_path),
        "-c",
        "copy",
        "-map",
        "0",
        "-map",
        "1",
        "-acodec",
        "aac",
        "-map",
        "2",
        "-scodec",
        "mov_text",
        str(output),
        "-y",
    ]
    run_ffmpeg_command(command)
    return output


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
