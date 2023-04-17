import subprocess
from pathlib import Path


def generate_test_subs(path: Path):
    content = """1
00:00:00,000 --> 00:00:00,800
Hello World!

2
00:00:00,900 --> 00:00:01,500
This is a test.
"""
    path.write_text(content, encoding="utf-8")


def generate_test_audio(path: Path, freq: int = 1000, duration: float = 0.5) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency={freq}:duration={duration}",
            str(path),
            "-y",
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def generate_test_video(path: Path, duration: float = 1.0, rate: float = 30.0):
    """Generate a short test video with FFmpeg (color + silent audio)."""
    subprocess.run(
        [
            "ffmpeg",
            "-f",
            "lavfi",
            "-i",
            f"color=c=blue:s=64x64:d={duration}",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency=1000:duration={duration}",
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            "-r",
            str(rate),
            str(path),
            "-y",
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
