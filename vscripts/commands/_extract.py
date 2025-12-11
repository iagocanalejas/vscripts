import logging
from copy import deepcopy
from pathlib import Path
from typing import Literal

from pyutils.paths import create_temp_dir
from vscripts.constants import TYPE_TO_FFMPEG_TYPE
from vscripts.data.language import find_language
from vscripts.data.streams import FileStreams
from vscripts.utils import SRT_FFMPEG_CODECS, get_output_file_path, run_ffmpeg_command, suffix_by_codec

logger = logging.getLogger("vscripts")


def extract(
    streams: FileStreams,
    *,
    track: int | None = None,
    stream_type: Literal["audio", "subtitle"] = "audio",
    output: Path | None = None,
    **_,
) -> FileStreams:
    """
    Extract a specific audio or subtitle track from a multimedia file using FFmpeg and save it as a new file.
    Args:
        streams (FileStreams): The FileStreams object representing the multimedia file to extract from.
        track (int | None): The index of the track to extract. None will extract all tracks of the specified type.
        stream_type (Literal["audio", "subtitle"], optional): The type of stream to extract. Default is "audio".
        output (Path | None): The path to save the output file.
    Returns: The FileStreams object with updated file path for the extracted stream.
    """
    is_audio = stream_type == "audio"
    stream_list = streams.audios if is_audio else streams.subtitles

    if len(stream_list) < 1:
        raise ValueError(f"no {stream_type} streams found in {streams.file_path=}, cannot extract")
    if track is not None and (track < 0 or track >= len(stream_list)):
        raise ValueError(f"invalid {stream_type} {track=} for {stream_list=}")
    if track is not None and not stream_list[track].file_path.is_file():
        raise ValueError(f"invalid {stream_type} stream file path {stream_list[track].file_path=}")
    if track is None and any(not s.file_path.is_file() for s in stream_list):
        raise ValueError(f"one or more {stream_type} stream file paths are invalid in {stream_list=}")
    if output is not None and not output.is_dir():
        raise ValueError(f"invalid {output=}")

    def inner_extract(index: int) -> None:
        stream = stream_list[index]
        suffix = suffix_by_codec(stream.codec_name, stream_type)

        temp_output = Path(temp_dir) / f"temp_extracted_{index}.{suffix}"
        logger.info(f"extracting {stream_type}={index} from {streams.file_path.name}\n\toutputing to {temp_output}")

        command = [
            "-i",
            str(streams.file_path),
            "-map",
            f"0:{TYPE_TO_FFMPEG_TYPE[stream_type]}:{index}",
            "-map_metadata",
            "0",
        ]

        if stream.codec_name and stream.codec_name.lower() in SRT_FFMPEG_CODECS:
            command += ["-c:s", "srt"]
        else:
            command += ["-c", "copy"]

        command.append(str(temp_output))

        run_ffmpeg_command(command)

        og_path = stream.file_path
        stream.file_path = temp_output
        lang = find_language(stream)

        final_path = get_output_file_path(
            output or og_path.parent,
            default_name=f"{og_path.stem}_{lang}.{suffix}",
        )

        logger.info(f"moving extracted file to {final_path} with {lang=}")
        command = [
            "-i",
            str(temp_output),
            "-map",
            "0",
            "-c",
            "copy",
            "-map_metadata",
            "0",
            f"-metadata:s:{TYPE_TO_FFMPEG_TYPE[stream_type]}:0",
            f"language={lang}",
            str(final_path),
        ]
        run_ffmpeg_command(command)
        stream.file_path = final_path
        stream.ffmpeg_index = 0

    with create_temp_dir() as temp_dir:
        indices = range(len(stream_list)) if track is None else [track]
        for i in indices:
            inner_extract(i)

    return streams


def dissect(streams: FileStreams, *, output: Path | None = None, **_) -> FileStreams:
    """
    Dissect a multimedia file into its individual streams using FFmpeg and save them as separate files.
    Args:
        streams (FileStreams): The FileStreams object representing the multimedia file to dissect.
        output (Path | None): The directory to save the dissected streams.
    Returns: The FileStreams object with updated file paths for each dissected stream.
    """
    if not streams.file_path.is_file():
        raise ValueError(f"invalid {streams.file_path=}")

    output = output if output is not None else streams.file_path.parent
    if not output.exists():
        output.mkdir(parents=True, exist_ok=True)
    if not output.is_dir():
        raise ValueError(f"invalid {output=}")

    new_streams = FileStreams(
        video=deepcopy(streams.video) if streams.video else None,
        audios=[deepcopy(a) for a in streams.audios],
        subtitles=[deepcopy(s) for s in streams.subtitles],
    )

    if new_streams.video is not None:
        logger.info(f"extracting video stream ({new_streams.video.codec_name})")
        video_path = output / f"stream_{new_streams.video.index:03d}.mkv"
        command = [
            "-i",
            str(new_streams.file_path),
            "-map",
            "0:v:0",
            "-map_metadata",
            "0",
            "-c",
            "copy",
            str(video_path),
        ]
        run_ffmpeg_command(command)
        new_streams.video.file_path = video_path
        new_streams.video.ffmpeg_index = 0

    logger.info(f"extracting {len(new_streams.audios)} audio streams")
    for a_stream in new_streams.audios:
        logger.info(f"\t- audio stream {a_stream.index} ({a_stream.codec_name})")
        audio_path = output / f"stream_{a_stream.index:03d}.{suffix_by_codec(a_stream.codec_name, 'audio')}"
        command = [
            "-i",
            str(a_stream.file_path),
            "-map",
            f"0:a:{a_stream.ffmpeg_index}",
            "-map_metadata",
            "0",
            "-c",
            "copy",
            str(audio_path),
        ]
        run_ffmpeg_command(command)
        a_stream.file_path = audio_path
        a_stream.ffmpeg_index = 0

    logger.info(f"extracting {len(new_streams.subtitles)} subtitle streams")
    for s_stream in new_streams.subtitles:
        logger.info(f"\t- subtitle stream {s_stream.index} ({s_stream.codec_name})")
        subtitle_path = output / f"stream_{s_stream.index:03d}.{suffix_by_codec(s_stream.codec_name, 'subtitle')}"
        command = [
            "-i",
            str(s_stream.file_path),
            "-map",
            f"0:s:{s_stream.ffmpeg_index}",
            "-map_metadata",
            "0",
        ]

        if s_stream.codec_name and s_stream.codec_name.lower() in SRT_FFMPEG_CODECS:
            command += ["-c:s", "srt"]
        else:
            command += ["-c", "copy"]

        command.append(str(subtitle_path))
        run_ffmpeg_command(command)
        s_stream.file_path = subtitle_path
        s_stream.ffmpeg_index = 0

    return new_streams
