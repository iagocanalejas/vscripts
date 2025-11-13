from pathlib import Path

from vscripts.utils import run_ffmpeg_command


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


def generate_test_audio(path: Path, freq: int = 1000, duration: float = 0.5) -> Path:
    command = [
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency={freq}:duration={duration}",
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


def generate_test_full(tmp_path: Path, duration: float = 1.0, rate: float = 30.0) -> Path:
    video_path = tmp_path / "video.mp4"
    subs_path = tmp_path / "subs.srt"
    audio_path = tmp_path / "audio.mp3"
    generate_test_video(video_path, duration=duration, rate=rate)
    generate_test_audio(audio_path, duration=duration)
    generate_test_subs(subs_path)

    output = tmp_path / "full_video.mp4"

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
