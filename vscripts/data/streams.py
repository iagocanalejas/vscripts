import json
import logging
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Literal

from vscripts.constants import HDR_COLOR_TRANSFERS, UNKNOWN_LANGUAGE
from vscripts.data.language import ISO639_1_TO_3
from vscripts.utils import run_ffprobe_command

logger = logging.getLogger("vscripts")

CODEC_TYPE_VIDEO = "video"
CODEC_TYPE_AUDIO = "audio"
CODEC_TYPE_SUBTITLE = "subtitle"

CodecType = Literal["video", "audio", "subtitle"]


@dataclass
class FileStreams:
    video: "VideoStream | None" = None
    audios: list["AudioStream"] = field(default_factory=list)
    subtitles: list["SubtitleStream"] = field(default_factory=list)

    @property
    def file_path(self) -> Path:
        if self.video is not None:
            return self.video.file_path
        if self.audios:
            return self.audios[0].file_path
        if self.subtitles:
            return self.subtitles[0].file_path
        raise ValueError("no streams available to determine file path")

    @file_path.setter
    def file_path(self, value: Path) -> None:
        if self.video is not None:
            self.video.file_path = value
        for audio in self.audios:
            audio.file_path = value
        for subtitle in self.subtitles:
            subtitle.file_path = value

    @classmethod
    def from_file(cls, file_path: Path) -> "FileStreams":
        video: VideoStream | None = None
        audios: list[AudioStream] = []
        subtitles: list[SubtitleStream] = []

        data = _ffprobe_streams(file_path)
        for stream_data in data.get("streams", []):
            if stream_data.get("codec_type") == CODEC_TYPE_VIDEO:
                video = VideoStream.from_dict(stream_data)
                video.file_path = file_path
                video.format_names = data.get("format", {}).get("format_name", "").split(",")
                video.file_path = file_path
            elif stream_data.get("codec_type") == CODEC_TYPE_AUDIO:
                audio = AudioStream.from_dict(stream_data)
                audio.file_path = file_path
                audios.append(audio)
            elif stream_data.get("codec_type") == CODEC_TYPE_SUBTITLE:
                subtitle = SubtitleStream.from_dict(stream_data)
                subtitle.file_path = file_path
                subtitles.append(subtitle)

        return cls(
            video=video,
            audios=audios,
            subtitles=subtitles,
        )

    def copy(self, with_new_path: Path | None = None) -> "FileStreams":
        return FileStreams(
            video=self.video.copy(with_new_path=with_new_path) if self.video is not None else None,
            audios=[audio.copy(with_new_path=with_new_path) for audio in self.audios],
            subtitles=[subtitle.copy(with_new_path=with_new_path) for subtitle in self.subtitles],
        )


@dataclass
class Stream:
    index: int
    codec_name: str
    codec_type: CodecType
    file_path: Path = field(init=False)
    tags: dict[str, str] = field(default_factory=dict)


@dataclass
class VideoStream(Stream):
    duration: float | None = None
    format_names: list[str] | None = None
    r_frame_rate: float | None = None
    color_space: str = "bt709"
    color_transfer: str = "bt709"
    color_primaries: str = "bt709"

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
            duration=float(duration) if duration is not None else None,
            r_frame_rate=_parse_frame_rate(data.get("r_frame_rate")),
            codec_name=data["codec_name"],
            codec_type=data["codec_type"],
            color_space=data.get("color_space", "bt709"),
            color_transfer=data.get("color_transfer", "bt709"),
            color_primaries=data.get("color_primaries", "bt709"),
            tags=data.get("tags", {}),
        )

    @classmethod
    def from_file(cls, file_path: Path) -> "VideoStream | None":
        video_data = _ffprobe_streams(file_path, "v")
        streams = [cls.from_dict(data) for data in video_data.get("streams", [])]
        if len(streams) > 1:
            logger.warning(f"multiple video streams found in {file_path}, using the first one")
        if len(streams) == 0:
            return None
        stream = streams[0]
        stream.file_path = file_path
        stream.format_names = video_data.get("format", {}).get("format_name", "").split(",")
        return stream

    def copy(self, with_new_path: Path | None = None) -> "VideoStream":
        new_stream = deepcopy(self)
        if with_new_path is not None:
            new_stream.file_path = with_new_path
        return new_stream


@dataclass
class AudioStream(Stream):
    language: str = UNKNOWN_LANGUAGE
    duration: float | None = None
    bit_rate: int = 0
    sample_rate: int = 0
    channels: int = 0
    sample_fmt: str | None = None

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

        lang = data.get("tags", {}).get("language", UNKNOWN_LANGUAGE)
        if len(lang) < 3:
            logger.debug(f"found audio language tag: {lang}")
            ISO639_1_TO_3.get(lang, UNKNOWN_LANGUAGE)
        if lang in {"und", "unknown", "none", ""}:
            lang = UNKNOWN_LANGUAGE

        return AudioStream(
            index=data.get("index", -1),
            language=lang,
            duration=float(duration) if duration is not None else None,
            codec_name=data["codec_name"],
            codec_type=data["codec_type"],
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
        return streams

    @classmethod
    def from_file_stream(cls, file_path: Path, track: int = 0) -> "AudioStream":
        stream = cls.from_file(file_path)[int(track)]
        stream.file_path = file_path
        return stream

    def copy(self, with_new_path: Path | None = None) -> "AudioStream":
        new_stream = deepcopy(self)
        if with_new_path is not None:
            new_stream.file_path = with_new_path
        return new_stream


@dataclass
class SubtitleStream(Stream):
    language: str = UNKNOWN_LANGUAGE
    default: bool = False
    generated: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SubtitleStream":
        lang = data.get("tags", {}).get("language", UNKNOWN_LANGUAGE)
        if len(lang) < 3:
            logger.debug(f"found audio language tag: {lang}")
            ISO639_1_TO_3.get(lang, UNKNOWN_LANGUAGE)
        if lang in {"und", "unknown", "none", ""}:
            lang = UNKNOWN_LANGUAGE

        return SubtitleStream(
            index=data.get("index", -1),
            language=lang,
            codec_name=data["codec_name"],
            codec_type=data["codec_type"],
            tags=data.get("tags", {}),
        )

    @classmethod
    def from_file(cls, file_path: Path) -> list["SubtitleStream"]:
        subtitle_data = _ffprobe_streams(file_path, "s")
        streams = [cls.from_dict(data) for data in subtitle_data.get("streams", [])]
        for stream in streams:
            stream.file_path = file_path
        return streams

    @classmethod
    def from_file_stream(cls, file_path: Path, track: int = 0) -> "SubtitleStream":
        stream = cls.from_file(file_path)[int(track)]
        stream.file_path = file_path
        return stream

    def copy(self, with_new_path: Path | None = None) -> "SubtitleStream":
        new_stream = deepcopy(self)
        if with_new_path is not None:
            new_stream.file_path = with_new_path
        return new_stream


def _parse_duration(duration: str | None) -> float | None:
    if duration is None:
        return None
    if "," in duration:
        time_obj = datetime.strptime(duration[:15], "%H:%M:%S,%f")
    else:
        time_obj = datetime.strptime(duration[:15], "%H:%M:%S.%f")
    return timedelta(
        hours=time_obj.hour,
        minutes=time_obj.minute,
        seconds=time_obj.second,
        microseconds=time_obj.microsecond,
    ).total_seconds()


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


def _ffprobe_streams(file_path: Path, stream_type: Literal["v", "a", "s"] | None = None) -> dict[str, Any]:
    command = []
    if stream_type is not None:
        command += ["-select_streams", stream_type]
    command += [
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
