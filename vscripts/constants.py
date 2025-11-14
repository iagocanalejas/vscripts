import importlib.metadata
from typing import Literal

APP_NAME = "VScripts"
VERSION = importlib.metadata.version(APP_NAME.lower())

NTSC_RATE = 23.976
PAL_RATE = 25.0
NTSC_BROADCAST_RATE = 29.97

UNKNOWN_LANGUAGE = "unk"

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
COMMAND_APPEND_SUBS = "subs"
COMMAND_GENERATE_SUBS = "generate-subs"

ENCODING_1080P = "1080p"
ENCODING_2160P = "2160p"
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
