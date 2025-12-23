import logging
from pathlib import Path

from pyutils.lists import flatten
from vscripts.constants import NTSC_RATE, PAL_RATE
from vscripts.data.streams import AudioStream, VideoStream
from vscripts.utils import get_output_file_path, run_ffmpeg_command

logger = logging.getLogger("vscripts")


def atempo(
    input_path: Path,
    from_rate: float | None = None,
    to_rate: float = NTSC_RATE,
    *,
    track: int | None = None,
    output: Path | None = None,
    **_,
) -> list[Path]:
    """Adjust audio tempo based on a source and target frame rate.

    This function computes an `atempo` factor from the ratio of `to_rate` to `from_rate` and delegates the actual
    processing to `atempo_with`. If `from_rate` is not provided, it attempts to infer it from the input video stream's
    frame rate. If inference fails, a default PAL frame rate is used.

    Args:
        input_path: Path to the input media file.
        from_rate: Original frame rate of the media. If ``None``, the value is inferred from the video stream metadata
            when possible.
        to_rate: Target frame rate used to compute the tempo adjustment.
        track: Optional index of the audio track to process. If ``None``, all audio tracks are adjusted.
        output: Optional output file path or directory. If not provided, a default output path is generated.
        **_: Ignored keyword arguments (accepted for API compatibility).

    Returns:
        Path to the output media file with adjusted audio tempo.

    Raises:
        ValueError: If `input_path` does not exist or is not a file.
    """
    if not input_path.is_file():
        raise ValueError(f"invalid {input_path=}")

    if from_rate is None:
        stream = VideoStream.from_file(input_path)
        if stream is not None:
            if stream.r_frame_rate:
                logger.info(f"inferred from_rate={stream.r_frame_rate} from extra data")
                from_rate = float(stream.r_frame_rate)

    if from_rate is None:
        logger.warning("unable to infer from_rate from video stream")
        logger.info(f"using default from_rate={PAL_RATE}")
        from_rate = PAL_RATE

    return atempo_with(input_path, round(to_rate / from_rate, 8), track=track, output=output)


def atempo_with(
    input_path: Path,
    atempo_value: float,
    *,
    track: int | None = None,
    output: Path | None = None,
    **_,
) -> list[Path]:
    """Adjust audio tempo using a fixed atempo multiplier.

    This function applies an FFmpeg `atempo` filter to one or more audio streams in the input media file.
    The resulting file preserves metadata and updates stream duration information accordingly.

    Args:
        input_path: Path to the input media file.
        atempo_value: Tempo multiplier to apply. Values greater than 1.0 speed up audio, while values between
            0 and 1.0 slow it down. Must be non-negative.
        track: Optional index of the audio track to process. If ``None``, all audio tracks are adjusted.
        output: Optional output file path or directory. If not provided, a default output path is generated.
        **_: Ignored keyword arguments (accepted for API compatibility).

    Returns:
        List of paths to the output media files with adjusted audio tempo.

    Raises:
        ValueError: If `input_path` does not exist or is not a file.
        ValueError: If `atempo_value` is negative.
        ValueError: If the input file contains no audio streams.
        ValueError: If `track` is out of range for the available audio streams.
    """
    if not input_path.is_file():
        raise ValueError(f"invalid {input_path=}")
    if atempo_value < 0:
        raise ValueError(f"invalid atempo value {atempo_value=}, must be non-negative")

    streams = AudioStream.from_file(input_path)
    if len(streams) == 0:
        raise ValueError(f"input file {input_path} has no audio streams")
    if track is not None and (track < 0 or track >= len(streams)):
        raise ValueError(f"invalid audio {track=} for {streams=}")

    output = get_output_file_path(
        output or input_path.parent,
        default_name=f"{input_path.stem}_atempo_{atempo_value}{input_path.suffix}",
    )

    indices = range(len(streams)) if track is None else [track]

    command = ["-i", str(input_path)]
    command += flatten([[f"-filter:a:{i}", f"atempo={atempo_value}"] for i in indices])
    command += ["-map_metadata", "0"]
    command.append(str(output))

    logger.info(f"adjusting audio tempo of {input_path.name} by atempo={atempo_value}\n\toutputing to {output}")
    run_ffmpeg_command(command)
    return [output]


def atempo_video(
    input_path: Path,
    to_rate: float = NTSC_RATE,
    *,
    output: Path | None = None,
    **_,
) -> list[Path]:
    """Adjust video frame rate to change playback tempo.

    This function modifies the frame rate of the input video file to
    achieve a different playback tempo. It uses FFmpeg to set the
    desired frame rate and preserves metadata in the output file.

    Args:
        input_path: Path to the input video file.
        to_rate: Target frame rate to set for the video. Must be
            non-negative.
        output: Optional output file path or directory. If not provided,
            a default output path is generated.
        **_: Ignored keyword arguments (accepted for API compatibility).

    Returns:
        Path to the output video file with adjusted frame rate.

    Raises:
        ValueError: If `input_path` does not exist or is not a file.
        ValueError: If `to_rate` is negative.
        ValueError: If the input file contains no video streams.
    """
    if not input_path.is_file():
        raise ValueError(f"invalid {input_path=}")
    if to_rate < 0:
        raise ValueError(f"invalid to_rate {to_rate=}, must be non-negative")

    stream = VideoStream.from_file(input_path)
    if stream is None:
        raise ValueError(f"input file {input_path} has no video stream")

    suffix = f".{stream.format_names[0]}" if stream.format_names else input_path.suffix

    output = get_output_file_path(
        output or input_path.parent,
        default_name=f"{input_path.stem}_atempo_{1 / to_rate}{suffix}",
    )

    command = ["-i", str(input_path), "-r", f"{to_rate}", "-map_metadata", "0", str(output)]

    logger.info(f"adjusting video tempo of {input_path.name} to rate={to_rate}\n\toutputing to {output}")
    run_ffmpeg_command(command)
    return [output]
