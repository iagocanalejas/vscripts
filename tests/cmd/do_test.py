from unittest.mock import patch

import pytest
import torch
from vscripts.cli import cmd_do
from vscripts.utils import get_file_duration

from tests._utils import generate_test_audio, generate_test_full, test_whisper_model


@pytest.fixture(autouse=True)
def before_each():
    if torch.cuda.is_available():  # pragma: no cover
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()


@pytest.mark.cmd
def test_do_audio(tmp_path):
    audio_path = generate_test_audio(tmp_path / "audio.mp3", duration=2)
    output_path = tmp_path / "output.mp3"

    cmd_do(audio_path, ["atempo", "hasten=1"], output=output_path)

    assert output_path.exists(), "Output file should exist"
    assert output_path != audio_path, "Output file should be different from input"
    duration = get_file_duration(output_path)
    assert duration < 1.1, f"Expected duration smaller than 1s, got {duration}s"


@pytest.mark.cmd
def test_do_full_pipe(tmp_path):
    video_path = generate_test_full(tmp_path, duration=1)
    output_path = tmp_path / "output.mp4"

    with patch("vscripts.data.language.load_whisper", return_value=test_whisper_model):
        cmd_do(video_path, ["extract", "atempo", "delay=2", "append"], output=output_path)

    assert output_path.exists(), "Output file should exist"
    assert output_path != video_path, "Output file should be different from input"
    duration = get_file_duration(output_path)
    assert duration > 2.0, f"Expected duration greater than 2s, got {duration}s"


@pytest.mark.cmd
def test_do_inspect(tmp_path):
    video_path = generate_test_full(tmp_path, duration=1)
    output_path = tmp_path / "output.mp4"

    with patch("vscripts.data.language.load_whisper", return_value=test_whisper_model):
        cmd_do(video_path, ["inspect"], output=output_path)

    assert output_path.exists(), "Output file should exist"
    assert output_path != video_path, "Output file should be a new file"
    assert get_file_duration(output_path) == get_file_duration(video_path), "Durations should match"


@pytest.mark.cmd
def test_with_translate(tmp_path):
    video_path = generate_test_full(tmp_path, duration=1)
    output_path = tmp_path / "output.mp4"

    with patch("vscripts.data.language.load_whisper", return_value=test_whisper_model):
        cmd_do(video_path, ["extract=0", "generate-subs", "translate=es", "append"], output=output_path)

    assert output_path.exists(), "Output file should exist"
    assert output_path != video_path, "Output file should be different from input"
    duration = get_file_duration(output_path)
    assert duration > 0.9, f"Expected duration greater than 0.9s, got {duration}s"
