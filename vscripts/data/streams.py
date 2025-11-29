import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Literal

from vscripts.constants import HDR_COLOR_TRANSFERS
from vscripts.utils import run_ffprobe_command

logger = logging.getLogger("vscripts")

CODEC_TYPE_VIDEO = "video"
CODEC_TYPE_AUDIO = "audio"
CODEC_TYPE_SUBTITLE = "subtitle"

CodecType = Literal["video", "audio", "subtitle"]

# TODO: rewrite this as when we extract a video we can retrieve all the streams at once


@dataclass
class VideoStream:
    index: int
    file_path: Path = field(init=False)
    duration: str | None = None
    r_frame_rate: float | None = None
    codec_name: str | None = None
    codec_type: CodecType | None = None
    format_names: list[str] | None = None
    color_space: str = "bt709"
    color_transfer: str = "bt709"
    color_primaries: str = "bt709"
    tags: dict[str, str] = field(default_factory=dict)

    @property
    def is_hdr(self) -> bool:
        return self.color_transfer.lower() in HDR_COLOR_TRANSFERS

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VideoStream":
        duration = data.get("duration", None)
        if not duration and "DURATION" in data.get("tags", {}).keys():
            duration_time = data["tags"]["DURATION"]
            duration = _parse_duration(duration_time)

        return VideoStream(
            index=data.get("index", -1),
            duration=duration,
            r_frame_rate=_parse_frame_rate(data.get("r_frame_rate")),
            codec_name=data.get("codec_name"),
            codec_type=data.get("codec_type"),
            color_space=data.get("color_space", "bt709"),
            color_transfer=data.get("color_transfer", "bt709"),
            color_primaries=data.get("color_primaries", "bt709"),
            tags=data.get("tags", {}),
        )

    @classmethod
    def from_file(cls, file_path: Path) -> "VideoStream | None":
        video_data = _ffprobe_streams(file_path, "v")
        streams = [cls.from_dict(data) for data in video_data.get("streams", [])]
        if len(streams) == 0:
            return None
        stream = streams[0]
        stream.file_path = file_path
        stream.format_names = video_data.get("format", {}).get("format_name", "").split(",")
        return stream


@dataclass
class AudioStream:
    index: int
    bit_rate: int
    sample_rate: int
    channels: int
    sample_fmt: str | None
    language: str | None = None
    file_path: Path = field(init=False)
    duration: str | None = None
    codec_name: str | None = None
    codec_type: CodecType | None = None
    format_names: list[str] | None = None
    tags: dict[str, str] = field(default_factory=dict)

    @property
    def score(self) -> int:
        lossless_codecs = {"flac", "alac", "wavpack", "pcm_s16le", "pcm_s24le", "pcm_s32le", "pcm_s32be"}

        score = 0

        if self.codec_name in lossless_codecs:
            score += 10_000_000

        score += self.bit_rate
        fmt_score = {
            "pcm_s32le": 300000,
            "pcm_s32be": 300000,
            "pcm_s24le": 200000,
            "pcm_s16le": 100000,
        }
        score += fmt_score.get(self.sample_fmt or "", 0)
        score += self.sample_rate
        score += self.channels * 100

        return score

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AudioStream":
        duration = data.get("duration", None)
        if not duration and "DURATION" in data.get("tags", {}).keys():
            duration_time = data["tags"]["DURATION"]
            duration = _parse_duration(duration_time)

        return AudioStream(
            index=data.get("index", -1),
            codec_name=data.get("codec_name"),
            codec_type=data.get("codec_type"),
            duration=duration,
            bit_rate=int(data.get("bit_rate", 0) or 0),
            sample_rate=int(data.get("sample_rate", 0) or 0),
            channels=int(data.get("channels", 0) or 0),
            sample_fmt=data.get("sample_fmt", None),
            tags=data.get("tags", {}),
        )

    @classmethod
    def from_file(cls, file_path: Path) -> list["AudioStream"]:
        audio_data = _ffprobe_streams(file_path, "a")
        streams = [cls.from_dict(data) for data in audio_data.get("streams", [])]
        for stream in streams:
            stream.file_path = file_path
            stream.format_names = audio_data.get("format", {}).get("format_name", "").split(",")
        return streams

    @classmethod
    def from_file_stream(cls, file_path: Path, track: int = 0) -> "AudioStream":
        stream = cls.from_file(file_path)[int(track)]
        stream.file_path = file_path
        return stream


@dataclass
class SubtitleStream:
    index: int
    language: str | None = None
    file_path: Path = field(init=False)
    codec_name: str | None = None
    codec_type: CodecType | None = None
    format_names: list[str] | None = None
    tags: dict[str, str] = field(default_factory=dict)
    default: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SubtitleStream":
        return SubtitleStream(
            index=data.get("index", -1),
            codec_name=data.get("codec_name"),
            codec_type=data.get("codec_type"),
            tags=data.get("tags", {}),
        )

    @classmethod
    def from_file(cls, file_path: Path) -> list["SubtitleStream"]:
        subtitle_data = _ffprobe_streams(file_path, "s")
        streams = [cls.from_dict(data) for data in subtitle_data.get("streams", [])]
        for stream in streams:
            stream.file_path = file_path
            stream.format_names = subtitle_data.get("format", {}).get("format_name", "").split(",")
        return streams

    @classmethod
    def from_file_stream(cls, file_path: Path, track: int = 0) -> "SubtitleStream":
        stream = cls.from_file(file_path)[int(track)]
        stream.file_path = file_path
        return stream


def _parse_duration(duration: str | None) -> str | None:
    if duration is None:
        return None
    if "," in duration:
        time_obj = datetime.strptime(duration[:15], "%H:%M:%S,%f")
    else:
        time_obj = datetime.strptime(duration[:15], "%H:%M:%S.%f")
    return f"{
        timedelta(
            hours=time_obj.hour,
            minutes=time_obj.minute,
            seconds=time_obj.second,
            microseconds=time_obj.microsecond,
        ).total_seconds()
    }"


def _parse_frame_rate(frame_rate: str | None) -> float | None:
    if frame_rate is None:
        return None
    try:
        numerator, denominator = map(int, frame_rate.split("/"))
        if denominator == 0:
            return None
        return numerator / denominator
    except (ValueError, ZeroDivisionError):
        return None


def _ffprobe_streams(file_path: Path, stream_type: Literal["v", "a", "s"]) -> dict[str, Any]:
    command = [
        "-select_streams",
        stream_type,
        "-show_entries",
        "stream=index,duration,r_frame_rate,codec_name,codec_type,color_space,color_transfer,color_primaries,bit_rate,sample_rate,channels,sample_fmt",
        "-show_entries",
        "format=format_name",
        "-show_entries",
        "stream_tags",
        "-of",
        "json",
    ]
    result = run_ffprobe_command(file_path, command)
    result = json.loads(result)
    logger.debug(f"found '{stream_type}' stream =\n{json.dumps(result, indent=2)}")
    return result
