import importlib.metadata
from typing import Literal

APP_NAME = "VScripts"
VERSION = importlib.metadata.version(APP_NAME.lower())

NTSC_RATE = 23.976
PAL_RATE = 25.0
NTSC_BROADCAST_RATE = 29.97

UNKNOWN_LANGUAGE = "unk"
INVISIBLE_SEPARATOR = "<§§§>"

COMMAND_ATEMPO = "atempo"
COMMAND_ATEMPO_WITH = "atempo-with"
COMMAND_ATEMPO_VIDEO = "atempo-video"
COMMAND_DELAY = "delay"
COMMAND_HASTEN = "hasten"
COMMAND_REENCODE = "reencode"
COMMAND_EXTRACT = "extract"
COMMAND_INSPECT = "inspect"
COMMAND_DISSECT = "dissect"
COMMAND_APPEND = "append"
COMMAND_GENERATE_SUBS = "generate-subs"
COMMAND_TRANSLATE = "translate"

ENCODING_1080P: Literal["1080p"] = "1080p"
ENCODING_2160P: Literal["2160p"] = "2160p"
EncodingPreset = Literal["1080p", "2160p"]
ENCODING_PRESETS = {
    ENCODING_1080P: "H.265 NVENC 1080p",
    ENCODING_2160P: "H.265 NVENC 2160p 4K",
}

HDR_COLOR_TRANSFERS = [
    "smpte2084",
    "arib-std-b67",
    "bt2020-10",
    "bt2020-12",
]

ISO639_1_TO_3 = {
    "en": "eng",
    "fr": "fra",
    "de": "deu",
    "es": "spa",
    "gl": "glg",
    "it": "ita",
    "zh": "zho",
    "ja": "jpn",
}
ISO639_3_TO_1 = {v: k for k, v in ISO639_1_TO_3.items()}

TYPE_TO_FFMPEG_TYPE = {
    "video": "v",
    "audio": "a",
    "subtitle": "s",
}
