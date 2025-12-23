from pathlib import Path
from unittest.mock import patch

import pytest
from vscripts.commands._atempo import atempo, atempo_video, atempo_with

from tests._utils import generate_test_audio, generate_test_video, get_file_duration


def test_atempo_io():
    with pytest.raises(ValueError):
        atempo(Path("non_existent_file.wav"), from_rate=24.0, to_rate=30.0)

    with pytest.raises(ValueError):
        atempo_with(Path("non_existent_file.wav"), 0.5)

    with pytest.raises(ValueError):
        atempo_video(Path("non_existent_file.wav"), to_rate=30.0)


@pytest.mark.integration
def test_atempo_with_explicit_from_rate(tmp_path):
    input_file = generate_test_audio(tmp_path / "input.wav")
    output = tmp_path / "atempoed.mkv"

    output_file = atempo(input_file, from_rate=25.0, to_rate=30.0, output=output)[0]

    assert output_file.exists(), "Output file should exist"
    assert output_file != input_file, "Output file should be different from input"

    duration = get_file_duration(output)
    assert 0 < duration < 2.2, f"Expected shorter duration, got {duration}s"


@pytest.mark.integration
def test_atempo_infering_from_rate(tmp_path):
    input_file = generate_test_audio(tmp_path / "input.wav")
    output = tmp_path / "atempoed.mkv"

    with (
        patch(
            "vscripts.data.streams._ffprobe_streams",
            return_value={
                "streams": [
                    {
                        "index": 0,
                        "r_frame_rate": "25/1",
                        "codec_type": "video",
                        "codec_name": "hevc",
                        "tags": {"language": "eng"},
                    },
                    {"index": 1, "codec_type": "audio", "codec_name": "aac", "tags": {"language": "eng"}},
                ]
            },
        ),
    ):
        output_file = atempo(input_file, from_rate=None, to_rate=30.0, output=output)[0]

    assert output_file.exists(), "Output file should exist"
    assert output_file != input_file, "Output file should be different from input"

    duration = get_file_duration(output)
    assert 0 < duration < 2.2, f"Expected shorter duration, got {duration}s"


@pytest.mark.integration
def test_simple_atempo_default_value(tmp_path):
    input_file = generate_test_audio(tmp_path / "input.wav")
    output = tmp_path / "atempoed.mkv"

    output_file = atempo(input_file, to_rate=30.0, output=output)[0]

    assert output_file.exists(), "Output file should exist"
    assert output_file != input_file, "Output file should be different from input"

    duration = get_file_duration(output)
    assert 0 < duration < 2.2, f"Expected shorter duration, got {duration}s"


@pytest.mark.integration
def test_simple_atempo_with(tmp_path):
    input_file = generate_test_audio(tmp_path / "input.wav")
    output = tmp_path / "atempoed.mkv"

    output_file = atempo_with(input_file, atempo_value=1.5, output=output)[0]

    assert output_file.exists(), "Output file should exist"
    assert output_file != input_file, "Output file should be different from input"

    duration = get_file_duration(output)
    assert 0 < duration < 2.0, f"Expected shorter duration, got {duration}s"


@pytest.mark.integration
def test_simple_atempo_video(tmp_path):
    input_file = generate_test_video(tmp_path / "input.mp4")
    output_file = tmp_path / "tempoed.mp4"

    result = atempo_video(input_file, to_rate=25, output=output_file)[0]

    assert result.exists(), "Output file should exist"
    assert result != input_file, "Output should be a new file"

    duration = get_file_duration(result)
    assert 1 < duration < 1.1, f"Expected shorter video, got {duration}s"
