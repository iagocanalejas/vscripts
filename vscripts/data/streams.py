import json
import logging
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("vscripts")


@dataclass
class VideoStream:
    index: int
    file_path: Path = field(init=False)
    duration: str | None = None
    codec_name: str | None = None
    codec_type: str | None = None
    r_frame_rate: float | None = None
    tags: dict[str, str] = field(default_factory=dict)

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
            codec_name=data.get("codec_name"),
            codec_type=data.get("codec_type"),
            r_frame_rate=_parse_frame_rate(data.get("r_frame_rate")),
            duration=duration,
            tags=data.get("tags", {}),
        )

    @classmethod
    def from_file(cls, file_path: Path) -> "VideoStream | None":
        video_streams_data = _ffprobe_streams(file_path, "v")
        streams = [cls.from_dict(data) for data in video_streams_data]
        if len(streams) == 0:
            return None
        stream = streams[0]
        stream.file_path = file_path
        return stream


@dataclass
class AudioStream:
    index: int
    file_path: Path = field(init=False)
    duration: str | None = None
    codec_name: str | None = None
    codec_type: str | None = None
    r_frame_rate: float | None = None
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
        audio_streams_data = _ffprobe_streams(file_path, "a")
        streams = [cls.from_dict(data) for data in audio_streams_data]
        for stream in streams:
            stream.file_path = file_path
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
    codec_type: str | None = None
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
        subtitle_streams_data = _ffprobe_streams(file_path, "s")
        streams = [cls.from_dict(data) for data in subtitle_streams_data]
        for stream in streams:
            stream.file_path = file_path
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


def _ffprobe_streams(file_path: Path, stream_type: Literal["v", "a", "s"]) -> list[dict[str, Any]]:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            stream_type,
            "-of",
            "json",
            "-show_entries",
            "stream=index,duration,r_frame_rate,codec_name,codec_type",
            "-show_entries",
            "stream_tags",
            str(file_path),
        ],
        capture_output=True,
        text=True,
    )
    result = json.loads(result.stdout).get("streams", [])
    logger.info(f"found '{stream_type}' stream =\n{json.dumps(result, indent=2)}")
    return result
