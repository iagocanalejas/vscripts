from pathlib import Path
from unittest.mock import patch

import pytest
from vscripts.commands._atempo import atempo, atempo_video, atempo_with
from vscripts.data.streams import FileStreams

from tests._utils import generate_test_audio, generate_test_full, generate_test_video, get_file_duration


def test_atempo_io(tmp_path):
    streams = FileStreams.from_file(generate_test_full(tmp_path, duration=1))
    with pytest.raises(ValueError):
        streams.file_path = Path("non_existent_file.wav")
        atempo(streams, from_rate=24.0, to_rate=30.0)

    with pytest.raises(ValueError):
        streams.file_path = Path("non_existent_file.wav")
        atempo_with(streams, atempo_value=0.5)

    with pytest.raises(ValueError):
        streams.file_path = Path("non_existent_file.mp4")
        atempo_video(streams, to_rate=30.0)


@pytest.mark.integration
def test_atempo_with_explicit_from_rate(tmp_path):
    input_file = tmp_path / "video.mp4"
    output = tmp_path / "atempoed.mkv"
    generate_test_audio(input_file)

    _ = atempo(FileStreams.from_file(input_file), from_rate=25.0, to_rate=30.0, output=output)

    assert output.exists(), "Output file should exist"
    assert output != input_file, "Output file should be different from input"

    duration = get_file_duration(output)
    assert 0 < duration < 0.5, f"Expected shorter duration, got {duration}s"


@pytest.mark.integration
def test_atempo_infering_from_rate(tmp_path):
    input_file = tmp_path / "video.mp4"
    output = tmp_path / "atempoed.mkv"
    generate_test_audio(input_file)

    with (
        patch(
            "vscripts.data.streams._ffprobe_streams",
            return_value={
                "streams": [
                    {"r_frame_rate": "25/1", "codec_type": "video", "codec_name": "hevc", "tags": {"language": "eng"}},
                    {"codec_type": "audio", "codec_name": "aac", "tags": {"language": "eng"}},
                ]
            },
        ),
    ):
        _ = atempo(FileStreams.from_file(input_file), from_rate=None, to_rate=30.0, output=output)

    assert output.exists(), "Output file should exist"
    assert output != input_file, "Output file should be different from input"

    duration = get_file_duration(output)
    assert 0 < duration < 0.5, f"Expected shorter duration, got {duration}s"


@pytest.mark.integration
def test_simple_atempo_default_value(tmp_path):
    input_file = tmp_path / "input.wav"
    output = tmp_path / "atempoed.mkv"
    generate_test_audio(input_file)

    _ = atempo(FileStreams.from_file(input_file), to_rate=30.0, output=output)

    assert output.exists(), "Output file should exist"
    assert output != input_file, "Output file should be different from input"

    duration = get_file_duration(output)
    assert 0 < duration < 0.5, f"Expected shorter duration, got {duration}s"


@pytest.mark.integration
def test_simple_atempo_with(tmp_path):
    input_file = tmp_path / "input.wav"
    output = tmp_path / "atempoed.mkv"
    generate_test_audio(input_file)

    _ = atempo_with(FileStreams.from_file(input_file), atempo_value=1.5, output=output)

    assert output.exists(), "Output file should exist"
    assert output != input_file, "Output file should be different from input"

    duration = get_file_duration(output)
    assert 0 < duration < 0.5, f"Expected shorter duration, got {duration}s"


@pytest.mark.integration
def test_simple_atempo_video(tmp_path):
    input_file = tmp_path / "input.mp4"
    output_file = tmp_path / "tempoed.mp4"
    generate_test_video(input_file, duration=1.0, rate=30)

    result = atempo_video(FileStreams.from_file(input_file), to_rate=25, output=output_file)

    assert result.video is not None, "Result should have a video stream"
    assert result.video.file_path.exists(), "Output file should exist"
    assert result.video.file_path != input_file, "Output should be a new file"

    duration = get_file_duration(result.video.file_path)
    assert 1 < duration < 1.1, f"Expected shorter video, got {duration}s"
