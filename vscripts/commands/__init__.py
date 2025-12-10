from collections.abc import Callable

from vscripts.constants import (
    COMMAND_APPEND,
    COMMAND_ATEMPO,
    COMMAND_ATEMPO_VIDEO,
    COMMAND_ATEMPO_WITH,
    COMMAND_DELAY,
    COMMAND_EXTRACT,
    COMMAND_REENCODE,
    COMMAND_HASTEN,
    COMMAND_DISSECT,
    COMMAND_INSPECT,
    COMMAND_GENERATE_SUBS,
    COMMAND_TRANSLATE,
)
from vscripts.data.streams import FileStreams

from ._append import (
    append as append,
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

from ._generate import (
    generate_subtitles as generate_subtitles,
)

from ._merge import (
    merge as merge,
)

from ._translate import (
    translate_subtitles as translate_subtitles,
)

COMMANDS: dict[str, Callable[..., FileStreams]] = {
    COMMAND_APPEND: append,
    COMMAND_ATEMPO: atempo,
    COMMAND_ATEMPO_WITH: atempo_with,
    COMMAND_ATEMPO_VIDEO: atempo_video,
    COMMAND_EXTRACT: extract,
    COMMAND_DISSECT: dissect,
    COMMAND_DELAY: delay,
    COMMAND_HASTEN: hasten,
    COMMAND_INSPECT: inspect,
    COMMAND_REENCODE: reencode,
    COMMAND_GENERATE_SUBS: generate_subtitles,
    COMMAND_TRANSLATE: translate_subtitles,
}
