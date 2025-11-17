import logging
from pathlib import Path
from typing import Literal

from pyutils.paths import create_temp_dir
from vscripts.data.language import find_language
from vscripts.data.streams import AudioStream, SubtitleStream, VideoStream
from vscripts.utils import ffmpeg_copy_by_codec, get_output_file_path, run_ffmpeg_command, suffix_by_codec

logger = logging.getLogger("vscripts")


def extract(
    input_path: Path,
    track: int = 0,
    stream_type: Literal["audio", "subtitle"] = "audio",
    output: Path | None = None,
    **_,
) -> Path:
    """
    Extract a specific audio or subtitle track from a multimedia file using FFmpeg and save it as a new file.
    Args:
        input_path (Path): The path to the multimedia file from which to extract the track.
        stream_type (Literal["audio", "subtitle"], optional): The type of stream to extract. Default is "audio".
        track (int, optional): The index of the track to extract. Default is 0.
        output (Path | None): The path to save the output file.
    Returns: The path to the newly created file containing the extracted track.
    """
    if not input_path.is_file():
        raise ValueError(f"invalid {input_path=}")
    if output is not None and not output.is_dir():
        raise ValueError(f"invalid {output=}")

    StreamClass = AudioStream if stream_type == "audio" else SubtitleStream
    stream = StreamClass.from_file_stream(input_path, track)
    ffmpeg_type = "a" if stream_type == "audio" else "s"
    suffix = suffix_by_codec(stream.codec_name, stream_type)

    with create_temp_dir() as temp_dir:
        temp_output = Path(temp_dir) / f"temp_extracted.{suffix}"
        logger.info(f"extracting {stream_type} {track=} from {input_path.name}\n\toutputting to {temp_output}")
        command = ["-i", str(input_path), "-map", f"0:{ffmpeg_type}:{track}", "-map_metadata", "0"]
        command += ffmpeg_copy_by_codec(stream.codec_name)
        command.append(str(temp_output))

        run_ffmpeg_command(command)

        stream = StreamClass.from_file(temp_output)[0]
        lang = find_language(stream)

        output = get_output_file_path(
            output or input_path.parent,
            default_name=f"{input_path.stem}_{lang}.{suffix}",
        )

        logger.info(f"moving extracted file to {output} with {lang=}")
        command = [
            "-i",
            str(temp_output),
            "-map",
            "0",
            "-c",
            "copy",
            "-map_metadata",
            "0",
            f"-metadata:s:{ffmpeg_type}:0",
            f"language={lang}",
            str(output),
        ]
        run_ffmpeg_command(command)

    return output


def dissect(input_path: Path, output: Path | None = None, **_) -> Path:
    """
    Dissect a multimedia file into its individual streams using FFmpeg and save them as separate files.
    Args:
        input_path (Path): The path to the multimedia file to dissect.
        output (Path | None): The directory to save the dissected streams.
    Returns: The path to the directory containing the dissected streams.
    """
    if not input_path.is_file():
        raise ValueError(f"invalid {input_path=}")

    output = output if output is not None else input_path.parent
    if not output.is_dir():
        raise ValueError(f"invalid {output=}")

    video_stream = VideoStream.from_file(input_path)
    audio_streams = AudioStream.from_file(input_path)
    subtitle_streams = SubtitleStream.from_file(input_path)

    if video_stream is not None:
        logger.info(f"excracting video stream ({video_stream.codec_name})")
        command = [
            "-i",
            str(input_path),
            "-map",
            "0:v:0",
            "-map_metadata",
            "0",
            "-c",
            "copy",
            str(output / f"stream_{video_stream.index:03d}.{video_stream.codec_name}"),
        ]
        run_ffmpeg_command(command)

    logger.info(f"excracting {len(audio_streams)} audio streams")
    for stream in audio_streams:
        logger.info(f"\t- audio stream {stream.index} ({stream.codec_name})")
        command = [
            "-i",
            str(input_path),
            "-map",
            f"0:a:{stream.index - 1}",
            "-map_metadata",
            "0",
            "-c",
            "copy",
            str(output / f"stream_{stream.index:03d}.{suffix_by_codec(stream.codec_name, 'audio')}"),
        ]
        run_ffmpeg_command(command)

    logger.info(f"excracting {len(subtitle_streams)} subtitle streams")
    for stream in subtitle_streams:
        logger.info(f"\t- subtitle stream {stream.index} ({stream.codec_name})")
        command = [
            "-i",
            str(input_path),
            "-map",
            f"0:s:{stream.index - len(audio_streams) - 1}",
            "-map_metadata",
            "0",
        ]
        command += ffmpeg_copy_by_codec(stream.codec_name)
        command.append(str(output / f"stream_{stream.index:03d}.{suffix_by_codec(stream.codec_name, 'subtitle')}"))
        run_ffmpeg_command(command)

    return output
