import subprocess
from pathlib import Path

import pytest
from vscripts.commands._append import append
from vscripts.utils import FFPROBE_BASE_COMMAND

from tests._utils import generate_test_audio, generate_test_full, generate_test_subs


def test_append_io(tmp_path):
    existing_file = tmp_path / "existing.wav"
    generate_test_audio(existing_file)

    with pytest.raises(ValueError):
        append(Path("non_existent_file.wav"), existing_file)

    with pytest.raises(ValueError):
        append(existing_file, Path("non_existent_file.wav"))


@pytest.mark.integration
def test_simple_audio_append(tmp_path):
    root = generate_test_full(tmp_path, duration=1)
    attachment = generate_test_audio(tmp_path / "attachment.wav")
    output = tmp_path / "combined.mkv"

    assert root.exists() and attachment.exists()

    result = append(root, attachment, output=output)[0]

    assert result == output
    assert output.exists()

    out = subprocess.check_output(
        FFPROBE_BASE_COMMAND
        + [
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
def test_simple_subtitle_append(tmp_path):
    root = generate_test_full(tmp_path, duration=1)
    subtitles = generate_test_subs(tmp_path / "subs.srt")
    output = tmp_path / "combined.mkv"

    result = append(root, subtitles, output=output)[0]

    assert result == output
    assert output.exists()
    out = subprocess.check_output(
        FFPROBE_BASE_COMMAND
        + [
            "-select_streams",
            "s",
            "-show_entries",
            "stream=index",
            "-of",
            "csv=p=0",
            str(output),
        ]
    )
    subtitle_stream_lines = [line for line in out.decode().strip().splitlines() if line.strip()]
    assert len(subtitle_stream_lines) >= 2, f"expected >=2 subtitle streams, got {len(subtitle_stream_lines)}"
