from .commands import (
    append as append,
    append_subs as append_subs,
    atempo as atempo,
    atempo_video as atempo_video,
    delay as delay,
    extract as extract,
    hasten as hasten,
)

from .streams import (
    VideoStream as VideoStream,
    AudioStream as AudioStream,
    SubtitleStream as SubtitleStream,
)

from .constants import (
    COMMAND_APPEND as COMMAND_APPEND,
    COMMAND_APPEND_SUBS as COMMAND_APPEND_SUBS,
    COMMAND_ATEMPO as COMMAND_ATEMPO,
    COMMAND_ATEMPO_VIDEO as COMMAND_ATEMPO_VIDEO,
    COMMAND_DELAY as COMMAND_DELAY,
    COMMAND_EXTRACT as COMMAND_EXTRACT,
    COMMAND_HASTEN as COMMAND_HASTEN,
    NTSC_BROADCAST_RATE as NTSC_BROADCAST_RATE,
    NTSC_RATE as NTSC_RATE,
    PAL_RATE as PAL_RATE,
)

COMMANDS = {
    COMMAND_ATEMPO: atempo,
    COMMAND_ATEMPO_VIDEO: atempo_video,
    COMMAND_DELAY: delay,
    COMMAND_HASTEN: hasten,
    COMMAND_EXTRACT: extract,
    COMMAND_APPEND: append,
    COMMAND_APPEND_SUBS: append_subs,
}
