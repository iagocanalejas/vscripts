import subprocess
from pathlib import Path

import pytest
from vscripts.commands._append import append
from vscripts.data.streams import FileStreams
from vscripts.utils import FFPROBE_BASE_COMMAND

from tests._utils import generate_test_audio, generate_test_full, generate_test_subs


def test_append_io(tmp_path):
    existing_file = tmp_path / "existing.wav"
    generate_test_audio(existing_file)

    with pytest.raises(ValueError):
        streams = FileStreams.from_file(generate_test_full(tmp_path, duration=1))
        assert streams.video is not None, "Test file must have a video stream"
        streams.video.file_path = Path("non_existent_file.wav")
        append(streams)

    with pytest.raises(ValueError):
        streams = FileStreams.from_file(generate_test_full(tmp_path, duration=1))
        streams.audios[0].file_path = Path("non_existent_file.wav")
        append(streams)


@pytest.mark.integration
def test_simple_audio_append(tmp_path):
    root = generate_test_full(tmp_path, duration=1)
    attachment = generate_test_audio(tmp_path / "attachment.wav")
    output = tmp_path / "combined.mkv"

    root_streams = FileStreams.from_file(root)
    root_streams.audios.append(FileStreams.from_file(attachment).audios[0])

    result = append(root_streams, output=output)

    assert result.file_path == output
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
def test_audio_append_with_language(tmp_path):
    root = generate_test_full(tmp_path, duration=1)
    attachment = generate_test_audio(tmp_path / "attachment.wav")
    output = tmp_path / "combined.mkv"

    root_streams = FileStreams.from_file(root)
    attachment_stream = FileStreams.from_file(attachment).audios[0]
    attachment_stream.language = "spa"
    root_streams.audios.append(attachment_stream)

    result = append(root_streams, output=output)

    assert result.file_path == output
    assert output.exists()

    out = subprocess.check_output(
        FFPROBE_BASE_COMMAND
        + [
            "-select_streams",
            "a",
            "-show_entries",
            "stream=index:stream_tags=language",
            "-of",
            "csv=p=0",
            str(output),
        ]
    )
    audio_stream_lines = [line for line in out.decode().strip().splitlines() if line.strip()]
    assert len(audio_stream_lines) >= 2, f"expected >=2 audio streams, got {len(audio_stream_lines)}"
    languages = [line.split(",")[1] if "," in line else "" for line in audio_stream_lines]
    assert "spa" in languages, f"expected 'spa' language tag in audio streams, got {languages}"


@pytest.mark.integration
def test_simple_subtitle_append(tmp_path):
    root = generate_test_full(tmp_path, duration=1)
    subtitles = generate_test_subs(tmp_path / "subs.srt")

    root_streams = FileStreams.from_file(root)
    root_streams.subtitles.append(FileStreams.from_file(subtitles).subtitles[0])

    result = append(root_streams, output=tmp_path / "output.mkv")

    assert len(result.subtitles) >= 2, f"expected >=2 subtitle streams, got {len(result.subtitles)}"
    output = result.file_path
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


@pytest.mark.integration
def test_subtitle_append_with_language_and_default(tmp_path):
    root = generate_test_full(tmp_path, duration=1)
    subtitles = generate_test_subs(tmp_path / "subs.srt")

    root_streams = FileStreams.from_file(root)
    subtitle_stream = FileStreams.from_file(subtitles).subtitles[0]
    subtitle_stream.language = "fra"
    subtitle_stream.default = True
    root_streams.subtitles.append(subtitle_stream)

    result = append(root_streams, output=tmp_path / "output.mkv")

    assert len(result.subtitles) >= 2, f"expected >=2 subtitle streams, got {len(result.subtitles)}"
    output = result.file_path
    assert output.exists()
    out = subprocess.check_output(
        FFPROBE_BASE_COMMAND
        + [
            "-select_streams",
            "s",
            "-show_entries",
            "stream=index:stream_tags=language",
            "-of",
            "csv=p=0",
            str(output),
        ]
    )
    subtitle_stream_lines = [line for line in out.decode().strip().splitlines() if line.strip()]
    assert len(subtitle_stream_lines) >= 2, f"expected >=2 subtitle streams, got {len(subtitle_stream_lines)}"
    languages = [line.split(",")[1] if "," in line else "" for line in subtitle_stream_lines]
    assert "fra" in languages, f"expected 'fra' language tag in subtitle streams, got {languages}"
