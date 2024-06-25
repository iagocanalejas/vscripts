from .commands import (
    append as append,
    append_subs as append_subs,
    atempo as atempo,
    atempo_video as atempo_video,
    delay as delay,
    extract as extract,
    hasten as hasten,
)

COMMAND_ORDER = ["extract", "atempo", "atempo-video", "delay", "hasten", "append", "subs"]
COMMANDS = {
    "atempo": atempo,
    "atempo-video": atempo_video,
    "delay": delay,
    "hasten": hasten,
    "extract": extract,
    "append": append,
    "subs": append_subs,
}
