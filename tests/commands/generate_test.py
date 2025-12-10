from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from vscripts.commands import generate_subtitles
from vscripts.data.streams import FileStreams

from tests._utils import generate_test_audio, generate_test_full


def test_generate_io(tmp_path):
    streams = FileStreams.from_file(generate_test_full(tmp_path, duration=1))
    assert len(streams.audios) > 0, "Test file must have at least one audio stream"
    with pytest.raises(ValueError):
        streams.audios[0].file_path = Path("non_existent_file.wav")
        generate_subtitles(streams)


@pytest.mark.integration
def test_generate_subtitles(tmp_path):
    audio_file = tmp_path / "input.mka"
    generate_test_audio(audio_file, duration=5)

    fake_model = MagicMock()
    fake_model.transcribe.return_value = {
        "segments": [
            {"start": 0.0, "end": 1.2, "text": "Hello world"},
            {"start": 1.2, "end": 3.5, "text": "This is a test"},
        ]
    }

    streams = FileStreams.from_file(audio_file)
    assert len(streams.audios) == 1
    assert len(streams.subtitles) == 0

    with patch("vscripts.commands._generate.load_whisper", return_value=fake_model):
        output_streams = generate_subtitles(streams, language="eng")

    assert len(output_streams.subtitles) == 1
    output_file = output_streams.subtitles[0].file_path

    assert output_file.exists(), "Output subtitle file should exist"
    assert output_file.suffix == ".srt"

    content = output_file.read_text(encoding="utf-8")
    assert "1\n" in content
    assert "00:00:00,000 --> 00:00:" in content
    assert "Hello world" in content
    assert "This is a test" in content


@pytest.mark.integration
def test_generate_subtitles_inferring_language(tmp_path):
    audio_file = tmp_path / "input.wav"
    generate_test_audio(audio_file, duration=5)

    fake_model = MagicMock()
    fake_model.transcribe.return_value = {
        "segments": [
            {"start": 0.0, "end": 1.2, "text": "Hello world"},
            {"start": 1.2, "end": 3.5, "text": "This is a test"},
        ]
    }

    streams = FileStreams.from_file(audio_file)
    assert len(streams.audios) == 1
    assert len(streams.subtitles) == 0

    with patch("vscripts.commands._generate.load_whisper", return_value=fake_model):
        output_streams = generate_subtitles(streams)

    assert len(output_streams.subtitles) == 1
    output_file = output_streams.subtitles[0].file_path

    assert output_file.exists(), "Output subtitle file should exist"
    assert output_file.suffix == ".srt"

    content = output_file.read_text(encoding="utf-8")
    assert "1\n" in content
    assert "00:00:00,000 --> 00:00:" in content
    assert "Hello world" in content
    assert "This is a test" in content


@pytest.mark.integration
def test_generate_subtitles_multiple_audio_streams(tmp_path):
    audio_file = tmp_path / "input.mka"
    generate_test_audio(audio_file, duration=5, streams=2)

    fake_model = MagicMock()
    fake_model.transcribe.return_value = {
        "segments": [
            {"start": 0.0, "end": 1.2, "text": "Hello world"},
            {"start": 1.2, "end": 3.5, "text": "This is a test"},
        ]
    }

    streams = FileStreams.from_file(audio_file)
    assert len(streams.audios) == 2
    assert len(streams.subtitles) == 0

    streams.audios[0].language = "spa"
    streams.audios[1].language = "eng"

    with patch("vscripts.commands._generate.load_whisper", return_value=fake_model):
        output_streams = generate_subtitles(streams, track=1)

    assert len(output_streams.subtitles) == 1
    assert streams.audios[0] == output_streams.audios[0], "Original audio stream should remain unchanged"
    assert streams.audios[1] == output_streams.audios[1], "Original audio stream should remain unchanged"

    assert streams.subtitles[0].language == streams.audios[1].language, "Subtitle language should match audio language"

    output_file = output_streams.subtitles[0].file_path
    assert output_file.exists(), "Output subtitle file should exist"
    assert output_file.suffix == ".srt"

    content = output_file.read_text(encoding="utf-8")
    assert "1\n" in content
    assert "00:00:00,000 --> 00:00:" in content
    assert "Hello world" in content
    assert "This is a test" in content
