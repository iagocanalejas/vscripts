import json
import logging
from pathlib import Path

from pyutils.paths import create_temp_dir
from vscripts.constants import ENCODING_1080P, ENCODING_PRESETS, UNKNOWN_LANGUAGE, EncodingPreset
from vscripts.data.language import find_audio_language, find_subs_language
from vscripts.data.streams import AudioStream, FileStreams
from vscripts.utils import get_output_file_path, is_hdr, run_ffmpeg_command, run_handbrake_command
from vscripts.utils._utils import suffix_by_codec

from ._extract import extract

logger = logging.getLogger("vscripts")


def delay(
    streams: FileStreams,
    delay: float,
    *,
    track: int | None = None,
    output: Path | None = None,
    **_,
) -> FileStreams:
    """
    Apply an audio delay effect to a multimedia file using FFmpeg and save it as a new file.
    Args:
        streams (FileStreams): The FileStreams object representing the multimedia file to be processed.
        delay(float): The delay time in seconds.
        track (int | None): The index of the audio track to delay. None will apply the delay to all the audio streams.
        output (Path | None): The path to save the output file.
    Returns: The FileStreams object with updated file path and audio stream duration.
    """
    if len(streams.audios) < 1:
        raise ValueError(f"no audio streams found in {streams.file_path=}, cannot delay")
    if delay < 0:
        raise ValueError(f"invalid delay time {delay=}, must be non-negative")
    if track is not None and (track < 0 or track >= len(streams.audios)):
        raise ValueError(f"invalid audio {track=} for {streams.audios=}")
    if track is not None and not streams.audios[track].file_path.is_file():
        raise ValueError(f"invalid {streams.audios[track].file_path=}")
    if track is None and any(not a.file_path.is_file() for a in streams.audios):
        raise ValueError(f"one or more audio stream file paths are invalid in {streams.audios=}")

    suffix = suffix_by_codec(streams.audios[track].codec_name, "audio") if track is not None else "mka"
    output = get_output_file_path(
        output or streams.file_path.parent,
        default_name=f"{streams.file_path.stem}_delayed_{delay}.{suffix}",
    )

    logger.info(f"applying audio {delay=}ms to {streams.file_path.name}\n\toutputing to {output}")
    command = ["-i", str(streams.file_path)]

    indices = range(len(streams.audios)) if track is None else [track]
    for i in indices:
        command += [f"-filter:a:{i}", f"adelay={int(float(delay) * 1000)}:all=true"]
        streams.audios[i].ffmpeg_index = 0
        streams.audios[i].file_path = output
        _update_duration(streams.audios[i], delay)

    command += ["-strict", "experimental", str(output)]

    run_ffmpeg_command(command)
    return streams


def hasten(
    streams: FileStreams,
    hasten: float,
    *,
    track: int | None = None,
    output: Path | None = None,
    **_,
) -> FileStreams:
    """
    Adjust the playback speed of a multimedia file using FFmpeg and save it as a new file.
    Args:
        streams (FileStreams): The FileStreams object representing the multimedia file to be processed.
        hasten(float): The hasten factor to adjust playback speed. None will apply the hasten to all the audio streams.
        track (int | None): The index of the audio track to hasten.
        output (Path | None): The path to save the output file.
    Returns: The FileStreams object with updated file path and audio stream duration.
    """
    if len(streams.audios) < 1:
        raise ValueError(f"no audio streams found in {streams.file_path=}, cannot hasten")
    if hasten < 0:
        raise ValueError(f"invalid hasten factor {hasten=}, must be non-negative")
    if track is not None and (track < 0 or track >= len(streams.audios)):
        raise ValueError(f"invalid audio {track=} for {streams.audios=}")
    if track is not None and not streams.audios[track].file_path.is_file():
        raise ValueError(f"invalid {streams.audios[track].file_path=}")
    if track is None and any(not a.file_path.is_file() for a in streams.audios):
        raise ValueError(f"one or more audio stream file paths are invalid in {streams.audios=}")

    suffix = suffix_by_codec(streams.audios[track].codec_name, "audio") if track is not None else "mka"
    output = get_output_file_path(
        output or streams.file_path.parent,
        default_name=f"{streams.file_path.stem}_hastened_{hasten}.{suffix}",
    )

    # TODO: i think this is not working in all tracks if track is None
    logger.info(f"adjusting playback speed of {streams.file_path.name} by hasten={hasten}\n\toutputing to {output}")
    command = [
        "-ss",
        f"{hasten}",
        "-i",
        str(streams.file_path),
        "-map",
        "0:a" if track is None else f"0:a:{track}",
        "-c:a",
        "copy",
        "-strict",
        "experimental",
        str(output),
    ]

    indices = range(len(streams.audios)) if track is None else [track]
    for i in indices:
        streams.audios[i].ffmpeg_index = 0
        streams.audios[i].file_path = output
        _update_duration(streams.audios[i], -hasten)

    run_ffmpeg_command(command)
    return streams


def inspect(streams: FileStreams, output: Path | None = None, force_detection: bool = False) -> FileStreams:
    """
    Inspect a multimedia file to identify and add language metadata for audio and subtitle streams using FFmpeg.
    Args:
        streams (FileStreams): The FileStreams object representing the multimedia file to inspect.
        output (Path | None): The path to save the output file.
        force_detection (bool): Whether to force language detection even if metadata exists.
    Returns: The FileStreams object with updated language metadata and file path.
    """
    if not streams.file_path.is_file():
        raise ValueError(f"invalid {streams.file_path=}")

    output = get_output_file_path(
        output or streams.file_path.parent,
        default_name=f"{streams.file_path.stem}_inspected{streams.file_path.suffix}",
    )

    metadata = []
    found_metadata: dict[str, dict[str, str]] = {"audio": {}, "subtitle": {}}

    with create_temp_dir() as temp_dir:
        for i, a_stream in enumerate(streams.audios):
            logger.info(f"found audio stream: {a_stream}")
            streams = extract(streams, track=i, stream_type="audio", output=Path(temp_dir))
            lang = find_audio_language(a_stream, force_detection=force_detection)
            if lang != UNKNOWN_LANGUAGE:
                logger.info(f"identified audio stream language as: {lang}")
                metadata += [f"-metadata:s:a:{i}", f"language={lang}"]
            a_stream.language = lang
            found_metadata["audio"][str(i)] = lang

        for i, s_stream in enumerate(streams.subtitles):
            logger.info(f"found subtitle stream: {s_stream}")
            streams = extract(streams, track=i, stream_type="subtitle", output=Path(temp_dir))
            lang = find_subs_language(s_stream, force_detection=force_detection)
            if lang != UNKNOWN_LANGUAGE:
                logger.info(f"identified subtitle stream language as: {lang}")
                metadata += [f"-metadata:s:s:{i}", f"language={lang}"]
            s_stream.language = lang
            found_metadata["subtitle"][str(i)] = lang

    if not metadata:
        logger.info("no metadata to add, skipping processing")
        return streams

    logger.info(f"inspecting {streams.file_path.name}\n\toutputing to {output}")
    command = [
        "-i",
        str(streams.file_path),
        "-map",
        "0",
        "-c",
        "copy",
        *metadata,
        str(output),
    ]

    run_ffmpeg_command(command)
    logger.info(f"updated metadata: {json.dumps(found_metadata, indent=2)}")
    streams.file_path = output
    return streams


def reencode(
    streams: FileStreams,
    quality: EncodingPreset = ENCODING_1080P,
    *,
    output: Path | None = None,
    **_,
) -> FileStreams:
    """
    Re-encode a multimedia file using HandBrakeCLI with a specified quality preset and save it as a new file.
    Args:
        streams (FileStreams): The FileStreams object representing the multimedia file to re-encode.
        quality (EncodingPreset): The quality preset to use for re-encoding.
        output (Path | None): The path to save the output file.
    Returns: A tuple containing the path to the newly created re-encoded multimedia file and the FileStreams object.
    """
    if streams.video is None:
        raise ValueError(f"no video stream found in {streams.file_path=}, cannot re-encode")
    if not streams.video.file_path.is_file():
        raise ValueError(f"invalid {streams.file_path=}")

    output = get_output_file_path(
        output or streams.file_path.parent,
        default_name=f"{streams.file_path.stem}_{quality}.mkv",
    )

    logger.info(f"re-encoding {streams.file_path.name} with {quality=}\n\toutputing to {output}")
    command = [f"--preset={ENCODING_PRESETS[quality]}"]
    if is_hdr(streams.file_path):
        command += ["--colorspace=bt709"]

    run_handbrake_command(streams.file_path, output, command)
    streams.video.file_path = output
    return streams


def _update_duration(stream: AudioStream, change: float) -> None:
    if stream.duration is not None:
        stream.duration += change
