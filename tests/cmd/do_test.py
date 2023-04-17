import pytest
from vscripts.cli import cmd_do
from vscripts.commands._utils import get_file_duration

from tests._utils import generate_test_full


@pytest.mark.cmd
def test_do(tmp_path):
    video_path = generate_test_full(tmp_path, duration=1)
    output_path = tmp_path / "output.mp4"

    actions = ["extract", "atempo", "delay=2", "append"]
    cmd_do(video_path, actions, output=output_path)

    assert output_path.exists(), "Output file should exist"
    assert output_path != video_path, "Output file should be different from input"
    duration = get_file_duration(output_path)
    assert duration > 2.0, f"Expected duration greater than 2s, got {duration}s"
