import logging
import shutil
from collections import OrderedDict
from pathlib import Path
from typing import Any

from pyutils.paths import create_temp_dir
from vscripts.commands import COMMANDS, merge
from vscripts.constants import (
    COMMAND_ATEMPO,
    COMMAND_ATEMPO_VIDEO,
    COMMAND_ATEMPO_WITH,
    COMMAND_DELAY,
    COMMAND_EXTRACT,
    COMMAND_GENERATE_SUBS,
    COMMAND_HASTEN,
    COMMAND_INSPECT,
    COMMAND_TRANSLATE,
    NTSC_RATE,
)
from vscripts.data.matcher import NameMatcher
from vscripts.data.streams import FileStreams

logger = logging.getLogger("vscripts")


def cmd_do(input_path: Path, actions: list[str], output: Path | None, **kwargs) -> int:
    parsed_actions = _parse_actions(actions)
    logger.info(f"Actions: {parsed_actions}")

    if output is not None and input_path.is_dir() and not output.is_dir():
        raise ValueError(f"When input path is a directory, output path must also be a directory. Got {output=}")

    def inner_do(path: Path, output: Path | None) -> int:
        streams = FileStreams.from_file(path)
        if COMMAND_INSPECT in parsed_actions:
            if len(parsed_actions) > 1:
                logger.warning("The 'inspect' command should be used alone. Other commands will be ignored.")
            COMMANDS[COMMAND_INSPECT](streams, output=output, force_detection=kwargs.get("force_detection", False))
            return 0

        if COMMAND_EXTRACT in parsed_actions.keys() and parsed_actions[COMMAND_EXTRACT] is not None:
            extract_track = parsed_actions[COMMAND_EXTRACT]
            assert extract_track is not None
            kwargs["track"] = extract_track[0]
            parsed_actions[COMMAND_EXTRACT] = None

        last_streams = streams
        with create_temp_dir() as temp_dir:
            logger.info(f"processing {last_streams.file_path} using temporary directory {temp_dir}")
            for command, args in parsed_actions.items():
                logger.info(f"running command '{command}' with {args=} and {kwargs=}")

                fn = COMMANDS[command]
                if command == COMMAND_TRANSLATE:
                    last_streams = fn(
                        last_streams,
                        *args if args is not None else [],
                        mode=kwargs.get("translation_mode", "local"),
                        output=Path(temp_dir),
                        **kwargs,
                    )
                elif args is not None:
                    last_streams = fn(last_streams, *args, output=Path(temp_dir), **kwargs)
                else:
                    last_streams = fn(last_streams, output=Path(temp_dir), **kwargs)

                # after this commands a new subtitle track is added that should be used for further commands
                if command in {COMMAND_GENERATE_SUBS, COMMAND_TRANSLATE}:
                    kwargs["track"] = len(last_streams.subtitles) - 1
                    logger.info(f"track set to {kwargs['track']} for further commands")

            for f in [f for f in last_streams.all_paths if f != path]:
                file_output = output
                if file_output is None:
                    file_output = path.parent / f.name
                logger.info(f"moving processed file {f} to final output location {file_output}")
                shutil.move(f, file_output)
        return 0

    if input_path.is_dir():  # pragma: no cover
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


def cmd_merge(target_path: Path, data_path: Path, output: Path | None, **kwargs) -> int:
    if (target_path.is_file() and not data_path.is_file()) or (target_path.is_dir() and not data_path.is_dir()):
        raise ValueError("Both target and data paths must be of the same type (file or directory).")

    def inner_merge(target: Path, output: Path | None) -> int:
        data_file = data_path
        target_matcher = NameMatcher(str(target.name))
        if not data_file.is_file():  # pragma: no cover
            for f in data_path.iterdir():
                if NameMatcher(f.name).season_episode() == target_matcher.season_episode():
                    logger.info(f"matched {f.name} with {target.name}")
                    data_file = f
                    break
        if not data_file.is_file():
            raise ValueError(f"No matching data file found for target {target} in {data_path}")

        merge(
            target=FileStreams.from_file(target),
            data=FileStreams.from_file(data_file),
            output=output if output else target.parent / target_matcher.clean(),
        )
        return 0

    if target_path.is_dir():  # pragma: no cover
        res = 0
        for file in target_path.iterdir():
            if file.is_file():
                res += inner_merge(file, output=output)
        return res
    return inner_merge(target_path, output)
