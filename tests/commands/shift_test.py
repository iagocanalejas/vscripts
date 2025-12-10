import subprocess
from pathlib import Path

import pytest
from vscripts.commands._shift import delay, hasten, inspect, reencode
from vscripts.constants import ENCODING_1080P
from vscripts.data.streams import FileStreams, _ffprobe_streams

from tests._utils import (
    generate_test_audio,
    generate_test_full,
    generate_test_video,
    get_file_duration,
    has_audio,
    has_subtitles,
)


def test_shift_io(tmp_path):
    streams = FileStreams.from_file(generate_test_full(tmp_path, duration=1))
    assert streams.video is not None, "Test file must have a video stream"
    with pytest.raises(ValueError):
        streams.audios[0].file_path = Path("non_existent_file.wav")
        delay(streams, 0.5)

    with pytest.raises(ValueError):
        streams.audios[0].file_path = Path("non_existent_file.wav")
        hasten(streams, 1.5)

    with pytest.raises(ValueError):
        streams.video.file_path = Path("non_existent_file.mp4")
        reencode(streams, "1080p")

    with pytest.raises(ValueError):
        streams = FileStreams.from_file(generate_test_full(tmp_path, duration=1))
        streams.video = None
        reencode(streams, "1080p")


@pytest.mark.integration
def test_simple_delay(tmp_path):
    input_file = tmp_path / "input.wav"
    output_file = tmp_path / "output.wav"

    generate_test_audio(input_file)

    assert input_file.exists() and input_file.stat().st_size > 0
    streams = FileStreams.from_file(input_file)
    streams.audios[0].duration = None

    result = delay(streams, 0.25, output=output_file)

    assert result.audios[0].file_path == output_file
    assert output_file.exists()
    assert output_file.stat().st_size > 0
    assert get_file_duration(output_file) >= get_file_duration(input_file) + 0.2
    assert result.audios[0].duration is None


@pytest.mark.integration
def test_simple_hasten(tmp_path):
    input_file = tmp_path / "input.wav"
    output_file = tmp_path / "output.wav"

    generate_test_audio(input_file)

    assert input_file.exists() and input_file.stat().st_size > 0

    result = hasten(FileStreams.from_file(input_file), 0.25, output=output_file)

    assert result.audios[0].file_path == output_file
    assert output_file.exists()
    assert output_file.stat().st_size > 0
    assert get_file_duration(output_file) >= get_file_duration(input_file) - 0.3
    assert result.audios[0].duration is not None and result.audios[0].duration >= get_file_duration(input_file) - 0.3


@pytest.mark.integration
def test_inspect_adds_language_metadata(tmp_path):
    video_path = generate_test_full(tmp_path, duration=1)
    assert has_audio(video_path)
    assert has_subtitles(video_path)

    inspected_streams = inspect(FileStreams.from_file(video_path), force_detection=True)
    inspected_path = inspected_streams.file_path

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
    no_metadata_streams = inspect(FileStreams.from_file(empty_video))
    assert no_metadata_streams.file_path == empty_video, "Should return same path if no metadata added"


@pytest.mark.integration
def test_reencode(monkeypatch, tmp_path):
    real_run = subprocess.run

    def fake_run(cmd, *_, **__):
        if cmd[0].lower() == "ffprobe".lower():
            return real_run(cmd, capture_output=True, text=True, check=True)
        if "HandBrakeCLI".lower() == cmd[0].lower():
            # override preset to use CPU
            cmd = [c if not c.startswith("--preset=") else "--preset=Fast 1080p30" for c in cmd]
            cmd.extend(["--width=1280", "--height=720"])
        return real_run(cmd, text=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    monkeypatch.setattr(subprocess, "run", fake_run)

    input_file = generate_test_full(tmp_path, duration=2)
    output_file = tmp_path / "reencoded.mkv"

    result = reencode(FileStreams.from_file(input_file), ENCODING_1080P, output=output_file)

    assert result.file_path == output_file
    assert output_file.exists()
    assert output_file.stat().st_size > 0
