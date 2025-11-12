import logging
import shutil
from collections import OrderedDict
from pathlib import Path
from typing import Any

from pyutils.paths import create_temp_dir
from vscripts.commands import COMMANDS
from vscripts.constants import (
    COMMAND_APPEND,
    COMMAND_ATEMPO,
    COMMAND_ATEMPO_VIDEO,
    COMMAND_ATEMPO_WITH,
    COMMAND_DELAY,
    COMMAND_EXTRACT,
    COMMAND_HASTEN,
    COMMAND_INSPECT,
    NTSC_RATE,
)
from vscripts.data.models import ProcessingData

logger = logging.getLogger("vscripts")


def cmd_do(input_path: Path, actions: list[str], output: Path | None, **kwargs) -> int:
    parsed_actions = _parse_actions(actions)
    logger.info(f"Actions: {parsed_actions}")

    if output is not None and input_path.is_dir() and not output.is_dir():
        raise ValueError(f"When input path is a directory, output path must also be a directory. Got {output=}")

    def inner_do(path: Path, output: Path | None) -> int:
        if COMMAND_INSPECT in parsed_actions:
            if len(parsed_actions) > 1:
                logger.warning("The 'inspect' command should be used alone. Other commands will be ignored.")
            COMMANDS[COMMAND_INSPECT](path, output=output, force_detection=kwargs.get("force_detection", False))
            return 0

        track = 0
        if COMMAND_EXTRACT in parsed_actions:
            track_args = parsed_actions[COMMAND_EXTRACT]
            track = track_args[0] if track_args else 0
        data = ProcessingData.from_path(path, audio_track=track)

        last_path = path
        with create_temp_dir() as temp_dir:
            logger.info(f"using temporary directory {temp_dir}")
            for command, args in parsed_actions.items():
                logger.info(f"running command '{command}' in file {last_path} with args '{args}'")

                fn = COMMANDS[command]
                if command == COMMAND_APPEND and args is None:
                    last_path = fn(attachment=last_path, root=path, output=Path(temp_dir), extra=data)
                elif args is not None:
                    print(*args)
                    last_path = fn(last_path, *args, output=Path(temp_dir), extra=data)
                else:
                    last_path = fn(last_path, output=Path(temp_dir), extra=data)

            if output is None:
                output = path.parent / last_path.name
            shutil.move(last_path, output)
        return 0

    if input_path.is_dir():
        res = 0
        for file in input_path.iterdir():
            if file.is_file():
                res += inner_do(file, output=output)
        return res
    return inner_do(input_path, output=output)


def _parse_actions(actions: list[str]) -> OrderedDict[str, list[Any] | None]:
    parsed_actions: OrderedDict[str, list[Any] | None] = OrderedDict()
    for action in actions:
        if "=" in action:
            a, v = action.split("=")
            if a in [COMMAND_ATEMPO]:
                values = [float(t) for t in v.split(",")] if "," in v else [float(v), NTSC_RATE]
                assert len(values) == 2, f"{a} requires two values."
                parsed_actions[a] = values
            elif a in [COMMAND_DELAY, COMMAND_HASTEN, COMMAND_ATEMPO_WITH, COMMAND_ATEMPO_VIDEO, COMMAND_ATEMPO_VIDEO]:
                parsed_actions[a] = [float(v)]
            elif a in [COMMAND_EXTRACT]:
                parsed_actions[a] = [int(v)]
            else:
                parsed_actions[a] = [v]
        else:
            parsed_actions[action] = None
    return parsed_actions
