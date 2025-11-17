from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from vscripts.commands import generate_subtitles

from tests._utils import generate_test_audio, generate_test_full


def test_generate_io(tmp_path):
    with pytest.raises(ValueError):
        generate_subtitles(Path("non_existent_file.wav"))

    video = generate_test_full(tmp_path, duration=1)
    with pytest.raises(ValueError):
        generate_subtitles(video)


@pytest.mark.integration
def test_generate_subtitles(tmp_path):
    audio_file = tmp_path / "input.wav"
    generate_test_audio(audio_file, duration=5)

    # --- Fake Whisper model and transcription ---
    fake_model = MagicMock()
    fake_model.transcribe.return_value = {
        "segments": [
            {"start": 0.0, "end": 1.2, "text": "Hello world"},
            {"start": 1.2, "end": 3.5, "text": "This is a test"},
        ]
    }

    with patch("vscripts.commands._generate.load_whisper", return_value=fake_model):
        output_file = generate_subtitles(audio_file, language="en")

    assert output_file.exists(), "Output subtitle file should exist"
    assert output_file.suffix == ".srt"

    content = output_file.read_text(encoding="utf-8")
    assert "1\n" in content
    assert "00:00:00,000 --> 00:00:" in content
    assert "Hello world" in content
    assert "This is a test" in content
