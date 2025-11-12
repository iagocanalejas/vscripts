import subprocess
from pathlib import Path

import pytest
from vscripts.commands._append import append, append_subs
from vscripts.commands._utils import has_subtitles

from tests._utils import generate_test_audio, generate_test_subs, generate_test_video


def test_append_io(tmp_path):
    existing_file = tmp_path / "existing.wav"
    generate_test_audio(existing_file)

    with pytest.raises(ValueError):
        append(Path("non_existent_file.wav"), existing_file)

    with pytest.raises(ValueError):
        append(existing_file, Path("non_existent_file.wav"))

    with pytest.raises(ValueError):
        append_subs(Path("non_existent_file.srt"), existing_file)

    with pytest.raises(ValueError):
        append_subs(existing_file, Path("non_existent_file.wav"))


@pytest.mark.integration
def test_simple_append(tmp_path):
    root = tmp_path / "root.wav"
    attachment = tmp_path / "attachment.wav"
    output = tmp_path / "combined.mkv"

    for path, freq in [(root, 440), (attachment, 880)]:
        generate_test_audio(path, freq)

    assert root.exists() and attachment.exists()

    result = append(attachment, root, output)

    assert result == output
    assert output.exists()

    out = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "a",
            "-show_entries",
            "stream=index",
            "-of",
            "csv=p=0",
            str(output),
        ]
    )
    audio_stream_lines = [line for line in out.decode().strip().splitlines() if line.strip()]
    assert len(audio_stream_lines) >= 2, f"expected >=2 audio streams, got {len(audio_stream_lines)}"


@pytest.mark.integration
def test_append_subs_explicit_lang(tmp_path):
    video = tmp_path / "input.mp4"
    subs = tmp_path / "test.srt"
    output = tmp_path / "with_subs.mp4"
    generate_test_video(video)
    generate_test_subs(subs)

    result = append_subs(subs, video, lang="eng", output=output)

    assert result.exists(), "Output file should exist"
    assert result != video, "Output should be a new file"

    assert has_subtitles(result), "Output file should contain subtitle streams"


@pytest.mark.integration
def test_append_subs_no_lang(tmp_path):
    video = tmp_path / "input.mp4"
    subs = tmp_path / "test.srt"
    output = tmp_path / "with_subs.mp4"
    generate_test_video(video)
    generate_test_subs(subs)

    result = append_subs(subs, video, lang=None, output=output)

    assert result.exists(), "Output file should exist"
    assert result != video, "Output should be a new file"

    assert has_subtitles(result), "Output file should contain subtitle streams"


@pytest.mark.integration
def test_append_subs_no_mp4(tmp_path):
    video = tmp_path / "input.mkv"
    subs = tmp_path / "test.srt"
    output = tmp_path / "with_subs.mkv"
    generate_test_video(video)
    generate_test_subs(subs)

    result = append_subs(subs, video, lang="eng", output=output)

    assert result.exists(), "Output file should exist"
    assert result != video, "Output should be a new file"

    assert has_subtitles(result), "Output file should contain subtitle streams"
