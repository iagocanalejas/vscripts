from pathlib import Path
from collections.abc import Callable

from vscripts.constants import (
    COMMAND_APPEND,
    COMMAND_APPEND_SUBS,
    COMMAND_ATEMPO,
    COMMAND_ATEMPO_VIDEO,
    COMMAND_ATEMPO_WITH,
    COMMAND_DELAY,
    COMMAND_EXTRACT,
    COMMAND_HASTEN,
    COMMAND_DISSECT,
    COMMAND_INSPECT,
)

from ._append import (
    append as append,
    append_subs as append_subs,
)

from ._atempo import (
    atempo as atempo,
    atempo_with as atempo_with,
    atempo_video as atempo_video,
)

from ._extract import (
    extract as extract,
    dissect as dissect,
)

from ._shift import (
    delay as delay,
    hasten as hasten,
    inspect as inspect,
    reencode as reencode,
)

COMMANDS: dict[str, Callable[..., Path]] = {
    COMMAND_ATEMPO: atempo,
    COMMAND_ATEMPO_WITH: atempo_with,
    COMMAND_ATEMPO_VIDEO: atempo_video,
    COMMAND_DELAY: delay,
    COMMAND_HASTEN: hasten,
    COMMAND_EXTRACT: extract,
    COMMAND_INSPECT: inspect,
    COMMAND_DISSECT: dissect,
    COMMAND_APPEND: append,
    COMMAND_APPEND_SUBS: append_subs,
}
