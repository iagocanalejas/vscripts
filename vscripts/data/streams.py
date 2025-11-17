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
            time_obj = datetime.strptime(duration_time[:15], "%H:%M:%S.%f")
            duration = f"{
                timedelta(
                    hours=time_obj.hour,
                    minutes=time_obj.minute,
                    seconds=time_obj.second,
                    microseconds=time_obj.microsecond,
                ).total_seconds()
            }"

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
    file_path: Path = field(init=False)
    duration: str | None = None
    codec_name: str | None = None
    codec_type: CodecType | None = None
    r_frame_rate: float | None = None
    format_names: list[str] | None = None
    tags: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AudioStream":
        duration = data.get("duration", None)
        if not duration and "DURATION" in data.get("tags", {}).keys():
            duration_time = data["tags"]["DURATION"]
            time_obj = datetime.strptime(duration_time[:15], "%H:%M:%S.%f")
            duration = f"{
                timedelta(
                    hours=time_obj.hour,
                    minutes=time_obj.minute,
                    seconds=time_obj.second,
                    microseconds=time_obj.microsecond,
                ).total_seconds()
            }"

        return AudioStream(
            index=data.get("index", -1),
            codec_name=data.get("codec_name"),
            codec_type=data.get("codec_type"),
            duration=duration,
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
    file_path: Path = field(init=False)
    codec_name: str | None = None
    codec_type: CodecType | None = None
    format_names: list[str] | None = None
    tags: dict[str, str] = field(default_factory=dict)

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
        "stream=index,duration,r_frame_rate,codec_name,codec_type,color_space,color_transfer,color_primaries",
        "-show_entries",
        "format=format_name",
        "-show_entries",
        "stream_tags",
        "-of",
        "json",
    ]
    result = run_ffprobe_command(file_path, command)
    result = json.loads(result)
    logger.info(f"found '{stream_type}' stream =\n{json.dumps(result, indent=2)}")
    return result
