import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest
from vscripts.commands import merge
from vscripts.commands._merge import _retrieve_data_streams, _retrieve_target_streams
from vscripts.data.streams import AudioStream, SubtitleStream, VideoStream
from vscripts.utils import FFPROBE_BASE_COMMAND, has_video

from tests._utils import (
    generate_test_audio,
    generate_test_full,
    generate_test_subs,
    generate_test_video,
)


def test_merge_io():
    with pytest.raises(ValueError):
        merge(Path("non_existent_file.wav"), Path("data_file.wav"), output=None)


@pytest.mark.integration
def test_merge_two_videos(tmp_path):
    target_path = generate_test_full(tmp_path, duration=1)
    data_path = generate_test_full(tmp_path, duration=1, output_name="data_video.mp4")
    video_stream = VideoStream.from_file(generate_test_video(tmp_path / "video_only.mp4", duration=1))
    audio1_stream = AudioStream.from_file(generate_test_audio(tmp_path / "audio1.mp3", duration=1))[0]
    audio2_stream = AudioStream.from_file(generate_test_audio(tmp_path / "audio2.mp3", duration=1))[0]
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
            return_value=(video_stream, [audio1_stream], [subs1_stream]),
        ),
        patch(
            "vscripts.commands._merge._retrieve_data_streams",
            return_value=([audio2_stream], [subs2_stream]),
        ),
    ):
        merged_output = merge(target_path, data_path, output=output_path)

    assert merged_output.exists()
    assert merged_output.stat().st_size > 0
    assert output_path == merged_output
    assert has_video(merged_output)

    out = subprocess.check_output(
        FFPROBE_BASE_COMMAND
        + [
            "-select_streams",
            "a",
            "-show_entries",
            "stream=index",
            "-of",
            "csv=p=0",
            str(merged_output),
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
            str(merged_output),
        ]
    )
    subtitle_stream_lines = [line for line in out.decode().strip().splitlines() if line.strip()]
    assert len(subtitle_stream_lines) >= 2, f"expected >=2 subtitle streams, got {len(subtitle_stream_lines)}"


@pytest.mark.integration
def test_merge_two_videos_forced_subs(tmp_path):
    target_path = generate_test_full(tmp_path, duration=1)
    data_path = generate_test_full(tmp_path, duration=1, output_name="data_video.mp4")
    video_stream = VideoStream.from_file(generate_test_video(tmp_path / "video_only.mp4", duration=1))
    audio1_stream = AudioStream.from_file(generate_test_audio(tmp_path / "audio1.mp3", duration=1))[0]
    audio2_stream = AudioStream.from_file(generate_test_audio(tmp_path / "audio2.mp3", duration=1))[0]
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
            return_value=(video_stream, [audio1_stream], [subs1_stream]),
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
        merged_output = merge(target_path, data_path, output=output_path)

    assert merged_output.exists()
    assert merged_output.stat().st_size > 0
    assert output_path == merged_output
    assert has_video(merged_output)

    out = subprocess.check_output(
        FFPROBE_BASE_COMMAND
        + [
            "-select_streams",
            "a",
            "-show_entries",
            "stream=index",
            "-of",
            "csv=p=0",
            str(merged_output),
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
            str(merged_output),
        ]
    )
    subtitle_stream_lines = [line for line in out.decode().strip().splitlines() if line.strip()]
    assert len(subtitle_stream_lines) >= 3, f"expected >=3 subtitle streams, got {len(subtitle_stream_lines)}"


@pytest.mark.integration
def test__retrieve_target_streams(tmp_path):
    video_stream = VideoStream.from_file(generate_test_video(tmp_path / "video_only.mp4", duration=1))
    audio_stream = AudioStream.from_file(generate_test_audio(tmp_path / "audio1.mp3", duration=1))[0]
    audio_stream.tags["language"] = "en"
    subs_stream = SubtitleStream.from_file(generate_test_subs(tmp_path / "subs1.srt"))[0]
    subs_stream.tags["language"] = "en"

    with (
        patch(
            "vscripts.commands._merge.VideoStream.from_file",
            return_value=video_stream,
        ),
        patch(
            "vscripts.commands._merge.AudioStream.from_file",
            return_value=[audio_stream],
        ),
        patch(
            "vscripts.commands._merge.SubtitleStream.from_file",
            return_value=[subs_stream],
        ),
    ):
        v_stream, a_streams, s_streams = _retrieve_target_streams(tmp_path)

    assert v_stream == video_stream
    assert a_streams == [audio_stream]
    assert s_streams == [subs_stream]


@pytest.mark.integration
def test__retrieve_data_streams(tmp_path):
    audio_stream = AudioStream.from_file(generate_test_audio(tmp_path / "audio1.mp3", duration=1))[0]
    audio_stream.tags["language"] = "es"
    subs_stream = SubtitleStream.from_file(generate_test_subs(tmp_path / "subs1.srt"))[0]
    subs_stream.tags["language"] = "es"

    with (
        patch(
            "vscripts.commands._merge.find_audio_language",
            return_value="spa",
        ),
        patch(
            "vscripts.commands._merge.find_subs_language",
            return_value="spa",
        ),
    ):
        a_streams, s_streams = _retrieve_data_streams(tmp_path)

    assert len(a_streams) == 1
    assert len(s_streams) == 1
