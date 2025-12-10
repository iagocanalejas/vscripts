import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest
from vscripts.commands import merge
from vscripts.commands._merge import _retrieve_data_streams, _retrieve_target_streams
from vscripts.data.streams import AudioStream, FileStreams, SubtitleStream
from vscripts.utils import FFPROBE_BASE_COMMAND

from tests._utils import (
    generate_test_audio,
    generate_test_full,
    generate_test_subs,
    has_video,
)


def test_merge_io(tmp_path):
    streams = FileStreams.from_file(generate_test_full(tmp_path, duration=1))
    assert streams.video is not None, "Test file must have a video stream"
    with pytest.raises(ValueError):
        streams.video.file_path = Path("non_existent_file.wav")
        merge(streams, streams, output=None)


@pytest.mark.integration
def test_merge_two_videos(tmp_path):
    target_path = generate_test_full(tmp_path, duration=1)
    data_path = generate_test_full(tmp_path, duration=1, output_name="data_video.mp4")
    audio1_stream = AudioStream.from_file(generate_test_audio(tmp_path / "audio1.mka", duration=1))[0]
    audio2_stream = AudioStream.from_file(generate_test_audio(tmp_path / "audio2.mka", duration=1))[0]
    subs1_stream = SubtitleStream.from_file(generate_test_subs(tmp_path / "subs1.srt"))[0]
    subs2_stream = SubtitleStream.from_file(generate_test_subs(tmp_path / "subs2.srt"))[0]

    audio1_stream.language = "eng"
    audio2_stream.language = "spa"
    subs1_stream.language = "eng"
    subs2_stream.language = "spa"

    output_path = tmp_path / "merged_output.mkv"

    with (
        patch(
            "vscripts.commands._merge._retrieve_target_streams",
            return_value=([audio1_stream], [subs1_stream]),
        ),
        patch(
            "vscripts.commands._merge._retrieve_data_streams",
            return_value=([audio2_stream], [subs2_stream]),
        ),
    ):
        merged_output = merge(FileStreams.from_file(target_path), FileStreams.from_file(data_path), output=output_path)

    assert merged_output.file_path.exists()
    assert merged_output.file_path.stat().st_size > 0
    assert output_path == merged_output.file_path
    assert has_video(merged_output.file_path)

    out = subprocess.check_output(
        FFPROBE_BASE_COMMAND
        + [
            "-select_streams",
            "a",
            "-show_entries",
            "stream=index",
            "-of",
            "csv=p=0",
            str(merged_output.file_path),
        ]
    )
    audio_stream_lines = [line for line in out.decode().strip().splitlines() if line.strip()]
    assert len(audio_stream_lines) >= 2, f"expected >=2 audio streams, got {len(audio_stream_lines)}"

    out = subprocess.check_output(
        FFPROBE_BASE_COMMAND
        + [
            "-select_streams",
            "s",
            "-show_entries",
            "stream=index",
            "-of",
            "csv=p=0",
            str(merged_output.file_path),
        ]
    )
    subtitle_stream_lines = [line for line in out.decode().strip().splitlines() if line.strip()]
    assert len(subtitle_stream_lines) >= 2, f"expected >=2 subtitle streams, got {len(subtitle_stream_lines)}"


@pytest.mark.integration
def test_merge_two_videos_forced_subs(tmp_path):
    target_path = generate_test_full(tmp_path, duration=1)
    data_path = generate_test_full(tmp_path, duration=1, output_name="data_video.mp4")
    audio1_stream = AudioStream.from_file(generate_test_audio(tmp_path / "audio1.mka", duration=1))[0]
    audio2_stream = AudioStream.from_file(generate_test_audio(tmp_path / "audio2.mka", duration=1))[0]
    subs1_stream = SubtitleStream.from_file(generate_test_subs(tmp_path / "subs1.srt"))[0]
    subs2_stream = SubtitleStream.from_file(generate_test_subs(tmp_path / "subs2.srt"))[0]
    subs3_stream = SubtitleStream.from_file(generate_test_subs(tmp_path / "subs3.srt"))[0]

    audio1_stream.language = "eng"
    audio2_stream.language = "spa"
    subs1_stream.language = "eng"
    subs2_stream.language = "spa"
    subs3_stream.language = "spa"
    subs3_stream.default = True

    output_path = tmp_path / "merged_output.mkv"

    with (
        patch(
            "vscripts.commands._merge._retrieve_target_streams",
            return_value=([audio1_stream], [subs1_stream]),
        ),
        patch(
            "vscripts.commands._merge._retrieve_data_streams",
            return_value=([audio2_stream], [subs2_stream]),
        ),
        patch(
            "vscripts.commands._merge._retrieve_forced_subs",
            return_value=subs3_stream,
        ),
    ):
        merged_output = merge(FileStreams.from_file(target_path), FileStreams.from_file(data_path), output=output_path)

    assert merged_output.file_path.exists()
    assert merged_output.file_path.stat().st_size > 0
    assert output_path == merged_output.file_path
    assert has_video(merged_output.file_path)

    out = subprocess.check_output(
        FFPROBE_BASE_COMMAND
        + [
            "-select_streams",
            "a",
            "-show_entries",
            "stream=index",
            "-of",
            "csv=p=0",
            str(merged_output.file_path),
        ]
    )
    audio_stream_lines = [line for line in out.decode().strip().splitlines() if line.strip()]
    assert len(audio_stream_lines) >= 2, f"expected >=2 audio streams, got {len(audio_stream_lines)}"

    out = subprocess.check_output(
        FFPROBE_BASE_COMMAND
        + [
            "-select_streams",
            "s",
            "-show_entries",
            "stream=index",
            "-of",
            "csv=p=0",
            str(merged_output.file_path),
        ]
    )
    subtitle_stream_lines = [line for line in out.decode().strip().splitlines() if line.strip()]
    assert len(subtitle_stream_lines) >= 3, f"expected >=3 subtitle streams, got {len(subtitle_stream_lines)}"


@pytest.mark.integration
def test__retrieve_target_streams(tmp_path):
    video = generate_test_full(tmp_path, duration=1)
    data = FileStreams.from_file(video)
    data.audios[0].language = "eng"
    data.subtitles[0].language = "eng"

    a_streams, s_streams = _retrieve_target_streams(data)

    assert a_streams == [data.audios[0]]
    assert s_streams == [data.subtitles[0]]


@pytest.mark.integration
def test__retrieve_data_streams(tmp_path):
    video = generate_test_full(tmp_path, duration=1)
    data = FileStreams.from_file(video)
    data.audios[0].tags["language"] = "es"
    data.subtitles[0].tags["language"] = "es"

    with (
        patch("vscripts.commands._merge.find_audio_language", return_value="spa"),
        patch("vscripts.commands._merge.find_subs_language", return_value="spa"),
    ):
        a_streams, s_streams = _retrieve_data_streams(data)

    assert len(a_streams) == 1
    assert len(s_streams) == 1
