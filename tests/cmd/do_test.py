from unittest.mock import patch

import pytest
from vscripts.cli import cmd_do
from vscripts.utils._utils import is_subs

from tests._utils import generate_test_audio, generate_test_full, get_file_duration

# TODO: verify output after shutil.move


@pytest.mark.cmd
def test_do_audio(tmp_path):
    audio_path = generate_test_audio(tmp_path / "audio.mp3", duration=2)
    output_path = tmp_path / "output.mp3"

    cmd_do(audio_path, ["atempo", "hasten=1"], output=output_path)

    assert output_path.exists(), "Output file should exist"
    assert output_path != audio_path, "Output file should be different from input"
    duration = get_file_duration(output_path)
    assert duration < 1.1, f"Expected duration smaller than 1.1s, got {duration}s"


@pytest.mark.cmd
def test_do_full_pipe(tmp_path):
    video_path = generate_test_full(tmp_path, duration=1)
    output_path = tmp_path / "output.mp4"

    cmd_do(video_path, ["extract", "atempo", "delay=2", "append"], output=output_path)

    assert output_path.exists(), "Output file should exist"
    assert output_path != video_path, "Output file should be different from input"
    duration = get_file_duration(output_path)
    assert duration > 2.0, f"Expected duration greater than 2s, got {duration}s"


@pytest.mark.cmd
def test_do_inspect(tmp_path):
    video_path = generate_test_full(tmp_path, duration=1)
    output_path = tmp_path / "output.mp4"

    cmd_do(video_path, ["inspect"], output=output_path)

    assert output_path.exists(), "Output file should exist"
    assert output_path != video_path, "Output file should be a new file"
    assert get_file_duration(output_path) == get_file_duration(video_path), "Durations should match"


@pytest.mark.cmd
def test_with_generate(tmp_path):
    video_path = generate_test_full(tmp_path, duration=1)
    output_path = tmp_path / "output.srt"

    subs = """1
00:00:00,000 --> 00:00:00,800
Hello world!

2
00:00:00,900 --> 00:00:01,500
This is a test.
"""

    with patch("vscripts.commands._generate._transcribe", return_value=subs):
        cmd_do(video_path, ["extract=0", "generate-subs", "append"], output=output_path)

    assert output_path.exists(), "Output file should exist"
    assert output_path != video_path, "Output file should be different from input"
    assert is_subs(output_path), "Output file should be a subtitle file"


@pytest.mark.cmd
def test_with_translate(tmp_path):
    video_path = generate_test_full(tmp_path, duration=1)
    output_path = tmp_path / "output.srt"

    subs = """1
00:00:00,000 --> 00:00:00,800
Hello world!

2
00:00:00,900 --> 00:00:01,500
This is a test.
"""

    subs_es = """1
00:00:00,000 --> 00:00:00,800
Hola mundo!

2
00:00:00,900 --> 00:00:01,500
Esto es un test.
"""

    with (
        patch("vscripts.commands._generate._transcribe", return_value=subs),
        patch("vscripts.commands._translate._translate_subtitles_helsinki", return_value=subs_es),
    ):
        cmd_do(video_path, ["extract=0", "generate-subs", "translate=spa", "append"], output=output_path)

    assert output_path.exists(), "Output file should exist"
    assert output_path != video_path, "Output file should be different from input"
    assert is_subs(output_path), "Output file should be a subtitle file"
