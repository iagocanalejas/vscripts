import subprocess
from pathlib import Path

import pytest
from vscripts.commands._extract import dissect, extract
from vscripts.commands._utils import has_audio, has_subtitles

from tests.commands._utils import generate_test_audio, generate_test_subs, generate_test_video


def test_extract_io():
    with pytest.raises(ValueError):
        extract(Path("non_existent_file.wav"))

    with pytest.raises(ValueError):
        dissect(Path("non_existent_file.wav"))


@pytest.mark.integration
def test_extract_audio_and_subs(tmp_path):
    video_path = tmp_path / "video.mp4"
    subs_path = tmp_path / "subs.srt"
    video_with_subs = tmp_path / "video_with_subs.mp4"

    generate_test_video(video_path, duration=1)
    generate_test_subs(subs_path)

    subprocess.run(
        [
            "ffmpeg",
            "-i",
            str(video_path),
            "-i",
            str(subs_path),
            "-c",
            "copy",
            "-map",
            "0",
            "-map",
            "1",
            "-scodec",
            "mov_text",
            str(video_with_subs),
            "-y",
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Ensure our input has both audio and subtitle tracks
    assert has_audio(video_with_subs)
    assert has_subtitles(video_with_subs)

    audio_out = extract(video_with_subs, stream_type="audio", track=0)
    assert audio_out.exists(), "Audio output file should exist"
    assert audio_out.suffix in {".mp3", ".aac", ".wav", ".m4a"}, f"Unexpected audio extension {audio_out.suffix}"
    assert has_audio(audio_out), "Extracted file should contain an audio stream"

    subs_out = extract(video_with_subs, stream_type="subtitle", track=0)
    assert subs_out.exists(), "Subtitle output file should exist"
    assert subs_out.suffix in {".srt", ".ass", ".vtt"}, f"Unexpected subtitle extension {subs_out.suffix}"
    content = subs_out.read_text(errors="ignore")
    assert "Hello" in content or len(content) > 0, "Subtitle file should contain text"

    with pytest.raises(ValueError):
        extract(video_with_subs, stream_type="video")  # type: ignore


@pytest.mark.integration
def test_dissect(tmp_path):
    video_path = tmp_path / "video.mp4"
    subs_path = tmp_path / "subs.srt"
    audio_path = tmp_path / "audio.mp3"
    video_with_subs = tmp_path / "video_with_subs.mp4"

    generate_test_video(video_path, duration=1)
    generate_test_audio(audio_path, duration=1)
    generate_test_subs(subs_path)

    subprocess.run(
        [
            "ffmpeg",
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
            str(video_with_subs),
            "-y",
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    output_dir = dissect(video_with_subs, output=tmp_path)

    assert output_dir.exists() and output_dir.is_dir(), "Output directory should exist"
    files = list(output_dir.glob("stream_*"))
    assert len(files) >= 3, f"Expected multiple output streams, found {len(files)}"

    for f in files:
        assert f.stat().st_size > 0, f"Stream file {f.name} should not be empty"
