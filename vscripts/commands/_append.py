import logging
from pathlib import Path

from vscripts.constants import UNKNOWN_LANGUAGE
from vscripts.data.streams import FileStreams
from vscripts.utils import get_output_file_path, run_ffmpeg_command

logger = logging.getLogger("vscripts")


def append(
    streams: FileStreams,
    *,
    output: Path | None = None,
    **_,
) -> FileStreams:
    """
    Appends multiple multimedia streams into a single file using FFmpeg.

    The function will use all the streams from the provided video file
    and one audio or subtitle stream for the rest of the files.
    Args:
        streams (FileStreams): The FileStreams object containing the multimedia streams to append.
        output (Path | None): The path to save the output file.
    Returns: The FileStreams object representing the newly created file.
    """
    if streams.video is not None and not streams.video.file_path.is_file():
        raise ValueError(f"invalid {streams.video.file_path=}")
    if any(not audio.file_path.is_file() for audio in streams.audios):
        raise ValueError("one or more invalid audio file paths")
    if any(not subtitle.file_path.is_file() for subtitle in streams.subtitles):
        raise ValueError("one or more invalid subtitle file paths")

    output = get_output_file_path(
        output or streams.file_path.parent,
        default_name=f"{streams.file_path.stem}_appended.mkv",
    )
    if output.suffix.lower() != ".mkv":
        raise ValueError("output file must be a MKV file")

    input_paths = []
    inputs = []
    maps = []
    metadata = []

    if streams.video is not None:
        inputs += ["-i", str(streams.video.file_path)]
        maps += ["-map", "0:v"]
        input_paths.append(streams.video.file_path)

    new_audio_index = 0
    for audio in streams.audios:
        if audio.file_path not in input_paths:
            inputs += ["-i", str(audio.file_path)]
            input_paths.append(audio.file_path)

        maps += ["-map", f"{input_paths.index(audio.file_path)}:a:{audio.ffmpeg_index}"]
        if audio.language != UNKNOWN_LANGUAGE:
            metadata += [f"-metadata:s:a:{new_audio_index}", f"language={audio.language}"]
        new_audio_index += 1

    new_subtitle_index = 0
    for subtitle in streams.subtitles:
        if subtitle.file_path not in input_paths:
            inputs += ["-i", str(subtitle.file_path)]
            input_paths.append(subtitle.file_path)

        maps += ["-map", f"{input_paths.index(subtitle.file_path)}:s:{subtitle.ffmpeg_index}"]
        if subtitle.language != UNKNOWN_LANGUAGE:
            metadata += [f"-metadata:s:s:{new_subtitle_index}", f"language={subtitle.language}"]
        if subtitle.default:
            metadata += [f"-disposition:s:{new_subtitle_index}", "default"]
        new_subtitle_index += 1

    for i in range(len(input_paths)):
        metadata += ["-map_metadata", f"{i}"]

    command = inputs + maps + metadata + [str(output)]

    logger.info(f"appending {input_paths}\n\toutputing to {output}")
    run_ffmpeg_command(command)
    return FileStreams.from_file(output)
