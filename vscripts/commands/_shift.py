import json
import logging
from pathlib import Path

from pyutils.lists import flatten
from pyutils.paths import create_temp_dir
from vscripts.constants import ENCODING_1080P, ENCODING_PRESETS, UNKNOWN_LANGUAGE, EncodingPreset
from vscripts.data.language import find_language
from vscripts.data.streams import AudioStream, SubtitleStream
from vscripts.utils import get_output_file_path, is_hdr, run_ffmpeg_command, run_handbrake_command
from vscripts.utils._utils import is_audio, is_subs, suffix_by_codec

from ._extract import dissect

logger = logging.getLogger("vscripts")


def delay(
    input_path: Path,
    delay: float,
    *,
    track: int | None = None,
    output: Path | None = None,
    **_,
) -> list[Path]:
    """
    Apply a delay to one or more audio tracks in a media file.

    This function uses FFmpeg to apply a specified delay (in seconds) to one or more audio tracks in a media file. If
    no track is specified, the delay is applied to all audio tracks.

    Args:
        input_path: Path to the input media file.
        delay: Delay time in seconds to apply to the audio track(s). Must be non-negative
        track: Optional index of the audio track to process. If ``None``, all audio tracks are adjusted.
        output: Optional output file path or directory. If not provided, a default output path is generated.
        **_: Ignored keyword arguments (accepted for API compatibility).

    Returns:
        A list containing the path to the output media file with adjusted audio delay.

    Raises:
        ValueError: If `input_path` does not exist or is not a file.
        ValueError: If `delay` is negative.
        ValueError: If `track` is out of range for the available audio streams.
    """
    if not input_path.is_file():
        raise ValueError(f"invalid {input_path=}")
    if delay < 0:
        raise ValueError(f"invalid delay time {delay=}, must be non-negative")

    streams = AudioStream.from_file(input_path)
    if len(streams) == 0:
        raise ValueError(f"input file {input_path} has no audio streams")
    if track is not None and (track < 0 or track >= len(streams)):
        raise ValueError(f"invalid audio {track=} for {streams=}")

    suffix = suffix_by_codec(streams[track].codec_name, "audio") if track is not None else "mka"
    output = get_output_file_path(
        output or input_path.parent,
        default_name=f"{input_path.stem}_delayed_{delay}.{suffix}",
    )

    indices = range(len(streams)) if track is None else [track]
    command = ["-i", str(input_path)]
    command += flatten([[f"-filter:a:{i}", f"adelay={int(float(delay) * 1000)}:all=true"] for i in indices])
    command += ["-strict", "experimental"]
    command.append(str(output))

    logger.info(f"applying audio {delay=}ms to {input_path.name}\n\toutputing to {output}")
    run_ffmpeg_command(command)
    return [output]


def hasten(
    input_path: Path,
    hasten: float,
    *,
    track: int | None = None,
    output: Path | None = None,
    **_,
) -> list[Path]:
    """
    Apply a hasten (negative delay) to one or more audio tracks in a media file.

    This function uses FFmpeg to apply a specified hasten (in seconds) to one or more audio tracks in a media file. If
    no track is specified, the hasten is applied to all audio tracks.

    Args:
        input_path: Path to the input media file.
        hasten: Hastening time in seconds to apply to the audio track(s). Must be non-negative
        track: Optional index of the audio track to process. If ``None``, all audio tracks are adjusted.
        output: Optional output file path or directory. If not provided, a default output path is generated.
        **_: Ignored keyword arguments (accepted for API compatibility).

    Returns:
        A list containing the path to the output media file with adjusted audio hasten.

    Raises:
        ValueError: If `input_path` does not exist or is not a file.
        ValueError: If `hasten` is negative.
        ValueError: If `track` is out of range for the available audio streams.
    """
    if not input_path.is_file():
        raise ValueError(f"invalid {input_path=}")
    if hasten < 0:
        raise ValueError(f"invalid delay time {delay=}, must be non-negative")

    streams = AudioStream.from_file(input_path)
    if len(streams) == 0:
        raise ValueError(f"input file {input_path} has no audio streams")
    if track is not None and (track < 0 or track >= len(streams)):
        raise ValueError(f"invalid audio {track=} for {streams=}")

    suffix = suffix_by_codec(streams[track].codec_name, "audio") if track is not None else "mka"
    output = get_output_file_path(
        output or input_path.parent,
        default_name=f"{input_path.stem}_hastened_{hasten}.{suffix}",
    )

    indices = range(len(streams)) if track is None else [track]
    command = ["-i", str(input_path), "-ss", f"{hasten}"]
    command += flatten([["-map", f"0:a:{i}"] for i in indices])
    command += ["-c:a", "copy", "-strict", "experimental"]
    command.append(str(output))

    logger.info(f"adjusting playback speed of {input_path.name} by {hasten=}\n\toutputing to {output}")
    run_ffmpeg_command(command)
    return [output]


def inspect(
    input_path: Path,
    *,
    force_detection: bool = False,
    output: Path | None = None,
    **_,
) -> list[Path]:
    """
    Inspect and update the metadata of audio and subtitle streams in a video file.

    This function analyzes the audio and subtitle streams of the specified video file to identify their languages.
    It updates the metadata of each stream with the detected language information. If no metadata updates are found,
    the function skips re-muxing the file.

    Args:
        input_path: Path to the input video file.
        force_detection: If ``True``, forces language detection even if metadata is already present.
            Defaults to ``False``.
        output: Optional output file path or directory. If not provided, a default output path is generated.
        **_: Ignored keyword arguments (accepted for API compatibility).

    Returns:
        A list containing the path to the inspected video file with updated metadata.

    Raises:
        ValueError: If `input_path` does not exist or is not a file.
    """
    if not input_path.is_file():
        raise ValueError(f"invalid {input_path=}")

    output = get_output_file_path(
        output or input_path.parent,
        default_name=f"{input_path.stem}_inspected{input_path.suffix}",
    )

    metadata = []
    found_metadata: dict[str, dict[str, str]] = {"audio": {}, "subtitle": {}}

    with create_temp_dir() as temp_dir:
        audio_idx = 0
        subtitle_idx = 0
        for f in dissect(input_path, skip_video=True, output=Path(temp_dir)):
            if not is_audio(f) and not is_subs(f):
                logger.warning(f"unrecognized stream type for extracted file: {f}")
                continue

            stream = AudioStream.from_file(f)[0] if is_audio(f) else SubtitleStream.from_file(f)[0]
            logger.info(f"found stream: {stream}")
            lang = find_language(stream, force_detection=force_detection)
            if isinstance(stream, AudioStream):
                if lang != UNKNOWN_LANGUAGE:
                    logger.info(f"identified audio stream language as: {lang}")
                    metadata += [f"-metadata:s:a:{audio_idx}", f"language={lang}"]
                found_metadata["audio"][str(audio_idx)] = lang
                audio_idx += 1
            else:
                if lang != UNKNOWN_LANGUAGE:
                    logger.info(f"identified subtitle stream language as: {lang}")
                    metadata += [f"-metadata:s:s:{subtitle_idx}", f"language={lang}"]
                found_metadata["subtitle"][str(subtitle_idx)] = lang
                subtitle_idx += 1

    if not metadata:
        logger.warning(f"no metadata updates found for {input_path}, skipping re-mux")
        return [input_path]

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

    logger.info(f"inspecting {input_path.name}\n\toutputing to {output}")
    logger.info(f"updated metadata: {json.dumps(found_metadata, indent=2)}")
    run_ffmpeg_command(command)
    return [output]


def reencode(
    input_path: Path,
    quality: EncodingPreset = ENCODING_1080P,
    *,
    output: Path | None = None,
    **_,
) -> list[Path]:
    """
    Re-encode a video file to a specified quality preset using HandBrake.

    Args:
        input_path: Path to the input video file.
        quality: Encoding preset to use for re-encoding. Defaults to ENCODING_1080P.
        output: Optional output file path or directory. If not provided, a default output path is generated.
        **_: Ignored keyword arguments (accepted for API compatibility).

    Returns:
        Path to the re-encoded video file.

    Raises:
        ValueError: If `input_path` does not exist or is not a file.
    """
    if not input_path.is_file():
        raise ValueError(f"invalid {input_path=}")

    output = get_output_file_path(
        output or input_path.parent,
        default_name=f"{input_path.stem}_{quality}.mkv",
    )

    command = [f"--preset={ENCODING_PRESETS[quality]}"]
    if is_hdr(input_path):
        command += ["--colorspace=bt709"]

    logger.info(f"re-encoding {input_path.name} with {quality=}\n\toutputing to {output}")
    run_handbrake_command(input_path, output, command)
    return [output]
