from pathlib import Path

import pytest
from vscripts.commands import translate_subtitles

from tests._utils import generate_test_full, generate_test_subs


def test_translate_io(tmp_path):
    with pytest.raises(ValueError):
        translate_subtitles(Path("non_existent_file.wav"), "es")

    video = generate_test_full(tmp_path, duration=1)
    with pytest.raises(ValueError):
        translate_subtitles(video, "fr")


@pytest.mark.integration
def test_translate_subtitles_basic(tmp_path):
    subs_file = generate_test_subs(tmp_path / "input.srt")
    output = tmp_path / "translated.srt"

    output = translate_subtitles(subs_file, "es", from_language="en", output=output)

    assert output.exists(), "Translated subtitle file should exist"
    assert output.suffix == ".srt", f"Unexpected extension: {output.suffix}"

    translated_text = output.read_text(errors="ignore")
    assert "00:00:00,000 --> 00" in translated_text
    assert "Hola Mundo" in translated_text, "Translated text must appear in output"
    assert "Hello world" not in translated_text


@pytest.mark.integration
def test_translate_subtitles_inferring_language(tmp_path):
    subs_file = generate_test_subs(tmp_path / "input.srt")
    output = tmp_path / "translated.srt"

    output = translate_subtitles(subs_file, "spa", output=output)

    assert output.exists(), "Translated subtitle file should exist"
    assert output.suffix == ".srt", f"Unexpected extension: {output.suffix}"

    translated_text = output.read_text(errors="ignore")
    assert "00:00:00,000 --> 00" in translated_text
    assert "Hola Mundo" in translated_text, "Translated text must appear in output"
    assert "Hello world" not in translated_text
