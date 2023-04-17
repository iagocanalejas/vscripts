from pathlib import Path

import pytest
from vscripts.commands._shift import delay, hasten, reencode
from vscripts.commands._utils import get_file_duration

from tests.commands._utils import generate_test_audio


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
