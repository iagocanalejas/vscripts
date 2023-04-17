import logging
from pathlib import Path
from typing import Literal

from vscripts.commands._utils import get_output_file_path, run_ffmpeg_command
from vscripts.data.language import find_audio_language, find_subs_language
from vscripts.data.streams import AudioStream, SubtitleStream, VideoStream

logger = logging.getLogger("vscripts")


def extract(
    input_path: Path,
    stream_type: Literal["audio", "subtitle"] = "audio",
    track: int = 0,
    output: Path | None = None,
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
    if not input_path.is_file() or not input_path.exists():
        raise ValueError(f"invalid {input_path=}")

    if stream_type == "audio":
        stream = AudioStream.from_file_stream(input_path, track)
        lang = find_audio_language(stream) or "unk"
    elif stream_type == "subtitle":
        stream = SubtitleStream.from_file_stream(input_path, track)
        lang = find_subs_language(stream) or "unk"
    else:
        raise ValueError(f"invalid {stream_type=}")

    suffix = stream.codec_name
    if not suffix:
        suffix = "m4a" if stream_type == "audio" else "srt"
    if stream_type == "subtitle" and suffix.lower() == "mov_text":
        suffix = "srt"

    if output is not None and not output.is_dir():
        raise ValueError(f"invalid {output=}")
    output = get_output_file_path(
        output or input_path.parent,
        default_name=f"{input_path.stem}_{lang}.{suffix}",
    )

    logger.info(f"extracting {stream_type} track {track} ({lang}) from {input_path}, outputting to {output}")
    command = ["ffmpeg", "-i", str(input_path), "-map", f"0:{'a' if stream_type == 'audio' else 's'}:{track}"]
    command += ["-c", "copy"] if stream_type == "audio" else ["-c:s", "srt"]
    command.append(str(output))
    logger.info(command)

    run_ffmpeg_command(command)
    return output


def dissect(input_path: Path, output: Path | None = None) -> Path:
    """
    Dissect a multimedia file into its individual streams using FFmpeg and save them as separate files.
    Args:
        input_path (Path): The path to the multimedia file to dissect.
        output (Path | None): The directory to save the dissected streams.
    Returns: The path to the directory containing the dissected streams.
    """
    if not input_path.is_file() or not input_path.exists():
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
            "ffmpeg",
            "-i",
            str(input_path),
            "-map",
            f"0:{video_stream.index}",
            "-c",
            "copy",
            str(output / f"stream_{video_stream.index:03d}.mp4"),
        ]
        logging.info(command)
        run_ffmpeg_command(command)

    logger.info(f"excracting {len(audio_streams)} audio streams")
    for stream in audio_streams:
        logger.info(f"\t- audio stream {stream.index} ({stream.codec_name})")
        command = [
            "ffmpeg",
            "-i",
            str(input_path),
            "-map",
            f"0:{stream.index}",
            "-c",
            "copy",
            str(output / f"stream_{stream.index:03d}.aac"),
        ]
        logging.info(command)
        run_ffmpeg_command(command)

    logger.info(f"excracting {len(subtitle_streams)} subtitle streams")
    for stream in subtitle_streams:
        logger.info(f"\t- subtitle stream {stream.index} ({stream.codec_name})")
        command = [
            "ffmpeg",
            "-i",
            str(input_path),
            "-map",
            f"0:{stream.index}",
            "-c:s",
            "srt",
            str(output / f"stream_{stream.index:03d}.srt"),
        ]
        logging.info(command)
        run_ffmpeg_command(command)

    return output
