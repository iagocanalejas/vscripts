from pathlib import Path
from unittest.mock import patch

import pytest
from vscripts.commands._extract import dissect, extract
from vscripts.data.streams import FileStreams

from tests._utils import generate_test_full, has_audio, has_subtitles


def test_extract_io(tmp_path):
    streams = FileStreams.from_file(generate_test_full(tmp_path, duration=1))
    assert streams.video is not None, "Test file must have a video stream"
    with pytest.raises(ValueError):
        streams.audios[0].file_path = Path("non_existent_file.wav")
        extract(streams)

    with pytest.raises(ValueError):
        streams.video.file_path = Path("non_existent_file.mp4")
        dissect(streams)


@pytest.mark.integration
def test_extract_audio_and_subs(tmp_path):
    video_path = generate_test_full(tmp_path, duration=1)
    assert has_audio(video_path)
    assert has_subtitles(video_path)

    with patch("vscripts.commands._extract.find_language", return_value="spa"):
        audio_streams = extract(FileStreams.from_file(video_path), track=0, stream_type="audio")
        subs_streams = extract(FileStreams.from_file(video_path), track=0, stream_type="subtitle")

    audio_out = audio_streams.audios[0]
    assert audio_out.file_path.exists(), "Audio output file should exist"
    assert audio_out.ffmpeg_index == 0, "Extracted audio stream index should be 0"
    assert has_audio(audio_out.file_path), "Extracted file should contain an audio stream"

    subs_out = subs_streams.subtitles[0]
    assert subs_out.file_path.exists(), "Subtitle output file should exist"
    assert subs_out.ffmpeg_index == 0, "Extracted subtitle stream index should be 0"
    content = subs_out.file_path.read_text(errors="ignore")
    assert "Hello" in content or len(content) > 0, "Subtitle file should contain text"


@pytest.mark.integration
def test_dissect(tmp_path):
    video_path = generate_test_full(tmp_path, duration=1)
    assert has_audio(video_path)
    assert has_subtitles(video_path)

    streams = dissect(FileStreams.from_file(video_path), output=tmp_path)

    files = list(tmp_path.glob("stream_*"))
    assert len(files) >= 3, f"Expected multiple output streams, found {len(files)}"

    for f in files:
        assert f.stat().st_size > 0, f"Stream file {f.name} should not be empty"

    assert streams.video is not None, "Dissected streams should include a video stream"
    assert streams.video.file_path.exists(), "Video stream file should exist"
    assert streams.video.ffmpeg_index == 0, "Video stream index should be 0"
    for i, audio in enumerate(streams.audios):
        assert audio.file_path.exists(), f"Audio stream {i} file should exist"
        assert audio.ffmpeg_index == 0, f"Audio stream {i} index should be 0"
    for i, subs in enumerate(streams.subtitles):
        assert subs.file_path.exists(), f"Subtitle stream {i} file should exist"
        assert subs.ffmpeg_index == 0, f"Subtitle stream {i} index should be 0"
