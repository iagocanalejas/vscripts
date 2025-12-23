from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from vscripts.commands import generate_subtitles

from tests._utils import generate_test_audio


def test_generate_io():
    with pytest.raises(ValueError):
        generate_subtitles(Path("non_existent_file.wav"))


@pytest.mark.integration
def test_generate_subtitles(tmp_path):
    audio_file = generate_test_audio(tmp_path / "input.mka", duration=5)

    fake_model = MagicMock()
    fake_model.transcribe.return_value = {
        "segments": [
            {"start": 0.0, "end": 1.2, "text": "Hello world"},
            {"start": 1.2, "end": 3.5, "text": "This is a test"},
        ]
    }

    with patch("vscripts.commands._generate.load_whisper", return_value=fake_model):
        output_files = generate_subtitles(audio_file, language="eng")

    assert len(output_files) == 1, "Should generate one subtitle file"
    output_file = output_files[0]
    assert output_file.exists(), "Output subtitle file should exist"
    assert output_file.suffix == ".srt"

    content = output_file.read_text(encoding="utf-8")
    assert "1\n" in content
    assert "00:00:00,000 --> 00:00:" in content
    assert "Hello world" in content
    assert "This is a test" in content


@pytest.mark.integration
def test_generate_subtitles_inferring_language(tmp_path):
    audio_file = generate_test_audio(tmp_path / "input.mka", duration=5)

    fake_model = MagicMock()
    fake_model.transcribe.return_value = {
        "segments": [
            {"start": 0.0, "end": 1.2, "text": "Hello world"},
            {"start": 1.2, "end": 3.5, "text": "This is a test"},
        ]
    }

    with patch("vscripts.commands._generate.load_whisper", return_value=fake_model):
        output_files = generate_subtitles(audio_file)

    assert len(output_files) == 1, "Should generate one subtitle file"
    output_file = output_files[0]
    assert output_file.exists(), "Output subtitle file should exist"
    assert output_file.suffix == ".srt"

    content = output_file.read_text(encoding="utf-8")
    assert "1\n" in content
    assert "00:00:00,000 --> 00:00:" in content
    assert "Hello world" in content
    assert "This is a test" in content


@pytest.mark.integration
def test_generate_subtitles_multiple_audio_streams(tmp_path):
    audio_file = generate_test_audio(tmp_path / "input.mka", duration=5, streams=2)

    fake_model = MagicMock()
    fake_model.transcribe.return_value = {
        "segments": [
            {"start": 0.0, "end": 1.2, "text": "Hello world"},
            {"start": 1.2, "end": 3.5, "text": "This is a test"},
        ]
    }

    with patch("vscripts.commands._generate.load_whisper", return_value=fake_model):
        output_files = generate_subtitles(audio_file, track=1)

    assert len(output_files) == 1, "Should generate one subtitle file for the specified track"
    output_file = output_files[0]
    assert output_file.exists(), "Output subtitle file should exist"
    assert output_file.suffix == ".srt"

    content = output_file.read_text(encoding="utf-8")
    assert "1\n" in content
    assert "00:00:00,000 --> 00:00:" in content
    assert "Hello world" in content
    assert "This is a test" in content
