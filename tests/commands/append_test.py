import subprocess
from pathlib import Path

import pytest
from vscripts.commands._append import append
from vscripts.data.streams import FileStreams
from vscripts.utils import FFPROBE_BASE_COMMAND

from tests._utils import generate_test_audio, generate_test_full


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
    root = tmp_path / "root.wav"
    attachment = tmp_path / "attachment.wav"
    output = tmp_path / "combined.mkv"

    for path, freq in [(root, 440), (attachment, 880)]:
        generate_test_audio(path, freq)

    assert root.exists() and attachment.exists()
    root = FileStreams.from_file(root)
    root.audios.append(FileStreams.from_file(attachment).audios[0])

    result = append(root, output=output)

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
