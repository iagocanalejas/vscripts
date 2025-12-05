import json
import logging
from pathlib import Path

from pyutils.paths import create_temp_dir
from vscripts.constants import ENCODING_1080P, ENCODING_PRESETS, UNKNOWN_LANGUAGE, EncodingPreset
from vscripts.data.language import find_audio_language, find_subs_language
from vscripts.data.streams import AudioStream, SubtitleStream
from vscripts.utils import get_output_file_path, is_hdr, run_ffmpeg_command, run_handbrake_command

from ._extract import extract

logger = logging.getLogger("vscripts")


def delay(
    input_path: Path,
    delay: float,
    *,
    output: Path | None = None,
    **_,
) -> Path:
    """
    Apply an audio delay effect to a multimedia file using FFmpeg and save it as a new file.
    Args:
        input_path (Path): The path to the audio or video file to be processed.
        delay(float): The delay time in seconds.
        output (Path | None): The path to save the output file.
    Returns: The path to the newly created file with the audio delay effect applied.
    """
    if not input_path.is_file():
        raise ValueError(f"invalid {input_path=}")

    output = get_output_file_path(
        output or input_path.parent,
        default_name=f"{input_path.stem}_delayed_{delay}{input_path.suffix}",
    )

    logger.info(f"applying audio {delay=}ms to {input_path.name}\n\toutputing to {output}")
    command = [
        "-i",
        str(input_path),
        "-af",
        f"adelay={int(float(delay) * 1000)}:all=true",
        "-strict",
        "experimental",
        str(output),
    ]

    run_ffmpeg_command(command)
    return output


def hasten(
    input_path: Path,
    hasten: float,
    *,
    output: Path | None = None,
    **_,
) -> Path:
    """
    Adjust the playback speed of a multimedia file using FFmpeg and save it as a new file.
    Args:
        input_path (Path): The path to the input audio or video file to adjust.
        hasten_factor (float): The hasten factor to adjust playback speed.
        output (Path | None): The path to save the output file.
    Returns: The path to the newly created hastened audio or video file.
    """
    if not input_path.is_file():
        raise ValueError(f"invalid {input_path=}")

    output = get_output_file_path(
        output or input_path.parent,
        default_name=f"{input_path.stem}_hastened_{hasten}{input_path.suffix}",
    )

    logger.info(f"adjusting playback speed of {input_path.name} by {hasten=}\n\toutputing to {output}")
    command = [
        "-i",
        str(input_path),
        "-ss",
        f"{hasten}",
        "-acodec",
        "copy",
        "-strict",
        "experimental",
        str(output),
    ]

    run_ffmpeg_command(command)
    return output


def inspect(input_path: Path, *, force_detection: bool = False, output: Path | None = None, **_) -> Path:
    """
    Inspect a multimedia file to identify and add language metadata for audio and subtitle streams using FFmpeg.
    Args:
        input_path (Path): The path to the input multimedia file.
        force_detection (bool): Whether to force language detection even if metadata exists.
        output (Path | None): The path to save the output file.
    Returns: The path to the newly created multimedia file with updated language metadata.
    """
    if not input_path.is_file():
        raise ValueError(f"invalid {input_path=}")

    output = get_output_file_path(
        output or input_path.parent,
        default_name=f"{input_path.stem}_inspected{input_path.suffix}",
    )

    metadata = []
    found_metadata: dict[str, dict[str, str]] = {"audio": {}, "subtitle": {}}

    audio_streams = AudioStream.from_file(input_path)
    with create_temp_dir() as temp_dir:
        for i, a_stream in enumerate(audio_streams):
            logger.info(f"found audio stream: {a_stream}")
            file = extract(input_path, track=i, stream_type="audio", output=Path(temp_dir))
            lang = find_audio_language(AudioStream.from_file(file)[0], force_detection=force_detection)
            if lang != UNKNOWN_LANGUAGE:
                logger.info(f"identified audio stream language as: {lang}")
                metadata += [f"-metadata:s:a:{i}", f"language={lang}"]
            found_metadata["audio"][str(i)] = lang

    subtitle_streams = SubtitleStream.from_file(input_path)
    with create_temp_dir() as temp_dir:
        for i, s_stream in enumerate(subtitle_streams):
            logger.info(f"found subtitle stream: {s_stream}")
            file = extract(input_path, track=i, stream_type="subtitle", output=Path(temp_dir))
            lang = find_subs_language(SubtitleStream.from_file(file)[0], force_detection=force_detection)
            if lang != UNKNOWN_LANGUAGE:
                logger.info(f"identified subtitle stream language as: {lang}")
                metadata += [f"-metadata:s:s:{i}", f"language={lang}"]
            found_metadata["subtitle"][str(i)] = lang

    if not metadata:
        logger.info("no metadata to add, skipping processing")
        return input_path

    logger.info(f"inspecting {input_path.name}\n\toutputing to {output}")
    command = [
        "-i",
        str(input_path),
        "-map",
        "0",
        "-c",
        "copy",
        *metadata,
        str(output),
    ]

    run_ffmpeg_command(command)
    logger.info(f"updated metadata: {json.dumps(found_metadata, indent=2)}")
    return output


def reencode(
    input_path: Path,
    quality: EncodingPreset = ENCODING_1080P,
    *,
    output: Path | None = None,
    **_,
) -> Path:
    """
    Re-encode a multimedia file using HandBrakeCLI with a specified quality preset and save it as a new file.
    Args:
        input_path (Path): The path to the input multimedia file.
        quality (EncodingPreset): The quality preset to use for re-encoding.
        output (Path | None): The path to save the output file.
    Returns: The path to the newly created re-encoded multimedia file.
    """
    if not input_path.is_file():
        raise ValueError(f"invalid {input_path=}")

    output = get_output_file_path(
        output or input_path.parent,
        default_name=f"{input_path.stem}_{quality}.mkv",
    )

    logger.info(f"re-encoding {input_path.name} with {quality=}\n\toutputing to {output}")
    command = [f"--preset={ENCODING_PRESETS[quality]}"]
    if is_hdr(input_path):
        command += ["--colorspace=bt709"]
    run_handbrake_command(input_path, output, command)
    return output
