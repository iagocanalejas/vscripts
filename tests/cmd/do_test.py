from unittest.mock import patch

import pytest
from vscripts.cli import cmd_do
from vscripts.commands._extract import extract
from vscripts.data.streams import AudioStream, SubtitleStream, VideoStream

from tests._utils import generate_test_audio, generate_test_full, get_file_duration, has_subtitles


@pytest.mark.cmd
def test_do_audio(tmp_path):
    audio_path = generate_test_audio(tmp_path / "audio.mka", duration=2)
    output_path = tmp_path / "output.mka"

    cmd_do(audio_path, ["atempo", "hasten=1"], output=output_path)

    assert output_path.exists(), "Output file should exist"
    assert output_path != audio_path, "Output file should be different from input"
    duration = get_file_duration(output_path)
    assert duration < 1.2, f"Expected duration smaller than 1.2s, got {duration}s"


@pytest.mark.cmd
def test_do_full_pipe(tmp_path):
    video_path = generate_test_full(tmp_path, duration=1)
    output_path = tmp_path / "output.mkv"

    cmd_do(video_path, ["extract", "atempo", "delay=2", "append", "inspect"], force_detection=True, output=output_path)

    assert output_path.exists(), "Output file should exist"
    assert output_path != video_path, "Output file should be different from input"

    assert VideoStream.from_file(output_path), "Output file should have a video stream"
    audio_streams = AudioStream.from_file(output_path)
    assert len(audio_streams) == 2, "Output file should have 2 audio streams"

    assert audio_streams[0].ffmpeg_index == 0, "First audio stream should have ffmpeg_index 0"
    assert audio_streams[1].ffmpeg_index == 1, "Second audio stream should have ffmpeg_index 1"
    assert audio_streams[0].language is not None, "First audio stream should have language metadata"
    assert audio_streams[1].language is not None, "Second audio stream should have language metadata"

    subtitle_streams = SubtitleStream.from_file(output_path)
    assert len(subtitle_streams) == 1, "Output file should have 1 subtitle streams"
    assert subtitle_streams[0].language is not None, "Subtitle stream should have language metadata"


@pytest.mark.cmd
def test_do_inspect(tmp_path):
    video_path = generate_test_full(tmp_path, duration=1)
    output_path = tmp_path / "output.mkv"

    cmd_do(video_path, ["inspect"], output=output_path)

    assert output_path.exists(), "Output file should exist"
    assert output_path != video_path, "Output file should be a new file"
    assert get_file_duration(output_path) == get_file_duration(video_path), "Durations should match"


@pytest.mark.cmd
def test_do_generate(tmp_path):
    video_path = generate_test_full(tmp_path, duration=1)
    output_path = tmp_path / "output.mkv"

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
    assert has_subtitles(output_path), "Output file should be a subtitle file"

    subtitle_streams = SubtitleStream.from_file(output_path)
    assert len(subtitle_streams) == 2, f"expected =2 subtitle streams, got {len(subtitle_streams)}"

    subs_path = extract(output_path, track=1, stream_type="subtitle", output=tmp_path)[0]
    content = subs_path.read_text(encoding="utf-8")
    assert "1\n" in content
    assert "Hello world!" in content
    assert "This is a test." in content


@pytest.mark.cmd
def test_do_translate(tmp_path):
    video_path = generate_test_full(tmp_path, duration=1)
    output_path = tmp_path / "output.mkv"

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
    assert has_subtitles(output_path), "Output file should be a subtitle file"

    subtitle_streams = SubtitleStream.from_file(output_path)
    assert len(subtitle_streams) == 2, f"expected =2 subtitle streams, got {len(subtitle_streams)}"

    subs_path = extract(output_path, track=1, stream_type="subtitle", output=tmp_path)[0]
    content = subs_path.read_text(encoding="utf-8")
    assert "1\n" in content
    assert "Hola mundo!" in content
    assert "Esto es un test." in content
