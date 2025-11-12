from pathlib import Path

import pytest
from vscripts.commands._extract import dissect, extract
from vscripts.commands._utils import has_audio, has_subtitles

from tests._utils import generate_test_full


def test_extract_io():
    with pytest.raises(ValueError):
        extract(Path("non_existent_file.wav"))

    with pytest.raises(ValueError):
        dissect(Path("non_existent_file.wav"))


@pytest.mark.integration
def test_extract_audio_and_subs(tmp_path):
    video_path = generate_test_full(tmp_path, duration=1)
    assert has_audio(video_path)
    assert has_subtitles(video_path)

    audio_out = extract(video_path, track=0, stream_type="audio")
    assert audio_out.exists(), "Audio output file should exist"
    assert audio_out.suffix in {".mp3", ".aac", ".wav", ".m4a"}, f"Unexpected audio extension {audio_out.suffix}"
    assert has_audio(audio_out), "Extracted file should contain an audio stream"

    subs_out = extract(video_path, track=0, stream_type="subtitle")
    assert subs_out.exists(), "Subtitle output file should exist"
    assert subs_out.suffix in {".srt", ".ass", ".vtt"}, f"Unexpected subtitle extension {subs_out.suffix}"
    content = subs_out.read_text(errors="ignore")
    assert "Hello" in content or len(content) > 0, "Subtitle file should contain text"


@pytest.mark.integration
def test_dissect(tmp_path):
    video_path = generate_test_full(tmp_path, duration=1)
    assert has_audio(video_path)
    assert has_subtitles(video_path)

    output_dir = dissect(video_path, output=tmp_path)

    assert output_dir.exists() and output_dir.is_dir(), "Output directory should exist"
    files = list(output_dir.glob("stream_*"))
    assert len(files) >= 3, f"Expected multiple output streams, found {len(files)}"

    for f in files:
        assert f.stat().st_size > 0, f"Stream file {f.name} should not be empty"
