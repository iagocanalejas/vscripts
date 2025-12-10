from pathlib import Path
from unittest.mock import patch

import pytest
from vscripts.commands import translate_subtitles
from vscripts.data.streams import FileStreams

from tests._utils import generate_test_full, generate_test_subs


def test_translate_io(tmp_path):
    streams = FileStreams.from_file(generate_test_full(tmp_path, duration=1))
    assert len(streams.subtitles) > 0, "Test file must have at least one subtitle stream"
    with pytest.raises(ValueError):
        streams.subtitles[0].file_path = Path("non_existent_file.wav")
        translate_subtitles(streams, "es")


@pytest.mark.integration
def test_translate_subtitles_basic(tmp_path):
    subs_file = generate_test_subs(tmp_path / "input.srt")
    output = tmp_path / "translated.srt"

    streams = FileStreams.from_file(subs_file)
    assert len(streams.subtitles) == 1

    output = translate_subtitles(streams, "spa", from_language="eng", output=output)

    assert len(output.subtitles) == 2
    output = output.subtitles[1].file_path

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

    streams = FileStreams.from_file(subs_file)
    assert len(streams.subtitles) == 1

    with patch("vscripts.commands._translate.find_subs_language", return_value="eng"):
        output = translate_subtitles(streams, "spa", output=output)

    assert len(output.subtitles) == 2
    output = output.subtitles[1].file_path

    assert output.exists(), "Translated subtitle file should exist"
    assert output.suffix == ".srt", f"Unexpected extension: {output.suffix}"

    translated_text = output.read_text(errors="ignore")
    assert "00:00:00,000 --> 00" in translated_text
    assert "Hola Mundo" in translated_text, "Translated text must appear in output"
    assert "Hello world" not in translated_text
