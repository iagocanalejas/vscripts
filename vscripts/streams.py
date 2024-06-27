import json
import subprocess
from dataclasses import dataclass, field


@dataclass
class VideoStream:
    index: int
    codec_name: str | None = None
    codec_long_name: str | None = None
    profile: str | None = None
    codec_type: str | None = None
    codec_time_base: str | None = None
    codec_tag_string: str | None = None
    codec_tag: str | None = None
    width: int | None = None
    height: int | None = None
    coded_width: int | None = None
    coded_height: int | None = None
    closed_captions: int | None = None
    has_b_frames: int | None = None
    sample_aspect_ratio: str | None = None
    display_aspect_ratio: str | None = None
    pix_fmt: str | None = None
    level: int | None = None
    color_range: str | None = None
    color_space: str | None = None
    color_transfer: str | None = None
    color_primaries: str | None = None
    chroma_location: str | None = None
    field_order: str | None = None
    timecode: str | None = None
    refs: int | None = None
    is_avc: str | None = None
    nal_length_size: str | None = None
    r_frame_rate: str | None = None
    avg_frame_rate: str | None = None
    time_base: str | None = None
    start_pts: int | None = None
    start_time: str | None = None
    duration_ts: int | None = None
    duration: str | None = None
    bit_rate: str | None = None
    max_bit_rate: str | None = None
    bits_per_raw_sample: int | None = None
    nb_frames: str | None = None
    disposition: dict[str, int] | None = field(default_factory=dict)
    tags: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "VideoStream":
        return VideoStream(
            index=data.get("index", None),
            codec_name=data.get("codec_name"),
            codec_long_name=data.get("codec_long_name"),
            profile=data.get("profile"),
            codec_type=data.get("codec_type"),
            codec_time_base=data.get("codec_time_base"),
            codec_tag_string=data.get("codec_tag_string"),
            codec_tag=data.get("codec_tag"),
            width=data.get("width"),
            height=data.get("height"),
            coded_width=data.get("coded_width"),
            coded_height=data.get("coded_height"),
            closed_captions=data.get("closed_captions"),
            has_b_frames=data.get("has_b_frames"),
            sample_aspect_ratio=data.get("sample_aspect_ratio"),
            display_aspect_ratio=data.get("display_aspect_ratio"),
            pix_fmt=data.get("pix_fmt"),
            level=data.get("level"),
            color_range=data.get("color_range"),
            color_space=data.get("color_space"),
            color_transfer=data.get("color_transfer"),
            color_primaries=data.get("color_primaries"),
            chroma_location=data.get("chroma_location"),
            field_order=data.get("field_order"),
            timecode=data.get("timecode"),
            refs=data.get("refs"),
            is_avc=data.get("is_avc"),
            nal_length_size=data.get("nal_length_size"),
            r_frame_rate=data.get("r_frame_rate"),
            avg_frame_rate=data.get("avg_frame_rate"),
            time_base=data.get("time_base"),
            start_pts=data.get("start_pts"),
            start_time=data.get("start_time"),
            duration_ts=data.get("duration_ts"),
            duration=data.get("duration"),
            bit_rate=data.get("bit_rate"),
            max_bit_rate=data.get("max_bit_rate"),
            bits_per_raw_sample=data.get("bits_per_raw_sample"),
            nb_frames=data.get("nb_frames"),
            disposition=data.get("disposition", {}),
            tags=data.get("tags", {}),
        )

    @classmethod
    def from_file(cls, file_path: str) -> "VideoStream":
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v",
                "-show_entries",
                "stream",
                "-of",
                "json",
                "-show_entries",
                "stream_tags",
                file_path,
            ],
            capture_output=True,
            text=True,
        )

        video_streams_data = json.loads(result.stdout).get("streams", [])
        return [cls.from_dict(data) for data in video_streams_data][0]


@dataclass
class AudioStream:
    index: int
    codec_name: str | None = None
    codec_long_name: str | None = None
    profile: str | None = None
    codec_type: str | None = None
    codec_time_base: str | None = None
    codec_tag_string: str | None = None
    codec_tag: str | None = None
    sample_fmt: str | None = None
    sample_rate: str | None = None
    channels: int | None = None
    channel_layout: str | None = None
    bits_per_sample: int | None = None
    r_frame_rate: str | None = None
    avg_frame_rate: str | None = None
    time_base: str | None = None
    start_pts: int | None = None
    start_time: str | None = None
    duration_ts: int | None = None
    duration: str | None = None
    bit_rate: str | None = None
    max_bit_rate: str | None = None
    nb_frames: str | None = None
    extradata_size: int | None = None
    disposition: dict[str, int] | None = field(default_factory=dict)
    tags: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "AudioStream":
        return AudioStream(
            index=data.get("index", None),
            codec_name=data.get("codec_name"),
            codec_long_name=data.get("codec_long_name"),
            profile=data.get("profile"),
            codec_type=data.get("codec_type"),
            codec_time_base=data.get("codec_time_base"),
            codec_tag_string=data.get("codec_tag_string"),
            codec_tag=data.get("codec_tag"),
            sample_fmt=data.get("sample_fmt"),
            sample_rate=data.get("sample_rate"),
            channels=data.get("channels"),
            channel_layout=data.get("channel_layout"),
            bits_per_sample=data.get("bits_per_sample"),
            r_frame_rate=data.get("r_frame_rate"),
            avg_frame_rate=data.get("avg_frame_rate"),
            time_base=data.get("time_base"),
            start_pts=data.get("start_pts"),
            start_time=data.get("start_time"),
            duration_ts=data.get("duration_ts"),
            duration=data.get("duration"),
            bit_rate=data.get("bit_rate"),
            max_bit_rate=data.get("max_bit_rate"),
            nb_frames=data.get("nb_frames"),
            extradata_size=data.get("extradata_size"),
            disposition=data.get("disposition", {}),
            tags=data.get("tags", {}),
        )

    @classmethod
    def from_file(cls, file_path: str) -> list["AudioStream"]:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "a",
                "-show_entries",
                "stream",
                "-of",
                "json",
                "-show_entries",
                "stream_tags",
                file_path,
            ],
            capture_output=True,
            text=True,
        )

        audio_streams_data = json.loads(result.stdout).get("streams", [])
        return [cls.from_dict(data) for data in audio_streams_data]

    @classmethod
    def from_file_stream(cls, file_path: str, track: int = 0) -> "AudioStream":
        return cls.from_file(file_path)[int(track)]


@dataclass
class SubtitleStream:
    index: int
    codec_name: str | None = None
    codec_long_name: str | None = None
    profile: str | None = None
    codec_type: str | None = None
    codec_time_base: str | None = None
    codec_tag_string: str | None = None
    codec_tag: str | None = None
    r_frame_rate: str | None = None
    avg_frame_rate: str | None = None
    time_base: str | None = None
    start_pts: int | None = None
    start_time: str | None = None
    duration_ts: int | None = None
    duration: str | None = None
    bit_rate: str | None = None
    max_bit_rate: str | None = None
    nb_frames: str | None = None
    disposition: dict[str, int] | None = field(default_factory=dict)
    tags: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "SubtitleStream":
        return SubtitleStream(
            index=data.get("index", None),
            codec_name=data.get("codec_name"),
            codec_long_name=data.get("codec_long_name"),
            profile=data.get("profile"),
            codec_type=data.get("codec_type"),
            codec_time_base=data.get("codec_time_base"),
            codec_tag_string=data.get("codec_tag_string"),
            codec_tag=data.get("codec_tag"),
            r_frame_rate=data.get("r_frame_rate"),
            avg_frame_rate=data.get("avg_frame_rate"),
            time_base=data.get("time_base"),
            start_pts=data.get("start_pts"),
            start_time=data.get("start_time"),
            duration_ts=data.get("duration_ts"),
            duration=data.get("duration"),
            bit_rate=data.get("bit_rate"),
            max_bit_rate=data.get("max_bit_rate"),
            nb_frames=data.get("nb_frames"),
            disposition=data.get("disposition", {}),
            tags=data.get("tags", {}),
        )

    @classmethod
    def from_file(cls, file_path: str) -> list["SubtitleStream"]:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "s",
                "-show_entries",
                "stream",
                "-of",
                "json",
                "-show_entries",
                "stream_tags",
                file_path,
            ],
            capture_output=True,
            text=True,
        )

        subtitle_streams_data = json.loads(result.stdout).get("streams", [])
        return [cls.from_dict(data) for data in subtitle_streams_data]

    @classmethod
    def from_file_stream(cls, file_path: str, track: int = 0) -> "SubtitleStream":
        return cls.from_file(file_path)[int(track)]
