from pathlib import Path

import pytest
from vscripts.commands._shift import delay, hasten, inspect, reencode
from vscripts.commands._utils import get_file_duration, has_audio, has_subtitles
from vscripts.data.streams import _ffprobe_streams

from tests._utils import generate_test_audio, generate_test_full, generate_test_video


def test_shift_io():
    with pytest.raises(ValueError):
        delay(Path("non_existent_file.wav"), 0.5)

    with pytest.raises(ValueError):
        hasten(Path("non_existent_file.wav"), 1.5)

    with pytest.raises(ValueError):
        reencode(Path("non_existent_file.wav"), "1080p")


@pytest.mark.integration
def test_simple_delay(tmp_path):
    input_file = tmp_path / "input.wav"
    output_file = tmp_path / "output.wav"

    generate_test_audio(input_file)

    assert input_file.exists() and input_file.stat().st_size > 0

    result = delay(input_file, 0.25, output_file)

    assert result == output_file
    assert output_file.exists()
    assert output_file.stat().st_size > 0
    assert get_file_duration(output_file) >= get_file_duration(input_file) + 0.2


@pytest.mark.integration
def test_simple_hasten(tmp_path):
    input_file = tmp_path / "input.wav"
    output_file = tmp_path / "output.wav"

    generate_test_audio(input_file)

    assert input_file.exists() and input_file.stat().st_size > 0

    result = hasten(input_file, 0.25, output_file)

    assert result == output_file
    assert output_file.exists()
    assert output_file.stat().st_size > 0
    assert get_file_duration(output_file) >= get_file_duration(input_file) - 0.3


@pytest.mark.integration
def test_inspect_adds_language_metadata(tmp_path):
    video_path = generate_test_full(tmp_path, duration=1)
    assert has_audio(video_path)
    assert has_subtitles(video_path)

    inspected_path = inspect(video_path, force_detection=True)

    assert inspected_path.exists(), "Output file should exist"
    assert inspected_path != video_path, "Output file should be a new file"

    audio_streams = _ffprobe_streams(inspected_path, "a").get("streams", [])
    subtitle_streams = _ffprobe_streams(inspected_path, "s").get("streams", [])

    for i, stream in enumerate(audio_streams):
        lang = stream.get("tags", {}).get("language")
        assert lang is not None, f"Audio stream {i} should have a language tag"
        assert isinstance(lang, str), f"Language tag for audio {i} must be a string"

    for i, stream in enumerate(subtitle_streams):
        lang = stream.get("tags", {}).get("language")
        assert lang is not None, f"Subtitle stream {i} should have a language tag"
        assert isinstance(lang, str), f"Language tag for subtitle {i} must be a string"


@pytest.mark.integration
def test_inspect_no_metadata_no_processing(tmp_path):
    empty_video = generate_test_video(tmp_path / "test_video2.mp4", duration=1)
    no_metadata_path = inspect(empty_video)
    assert no_metadata_path == empty_video, "Should return same path if no metadata added"
