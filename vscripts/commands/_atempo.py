import logging
from pathlib import Path

from vscripts.constants import NTSC_RATE, PAL_RATE
from vscripts.data.models import ProcessingData
from vscripts.data.streams import AudioStream, VideoStream
from vscripts.utils import get_output_file_path, has_audio, has_video, run_ffmpeg_command

logger = logging.getLogger("vscripts")


def atempo(
    input_path: Path,
    from_rate: float | None = None,
    to_rate: float = NTSC_RATE,
    output: Path | None = None,
    extra: ProcessingData | None = None,
) -> Path:
    """
    Change the audio tempo of a multimedia file using FFmpeg's atempo filter.
    Args:
        input_path (Path): The path to the input multimedia file.
        from_rate (float | None): The original frame rate of the video or inferred from the video stream.
        to_rate (float): The target frame rate to adjust the audio tempo to. Default is NTSC_RATE (29.97).
        output (Path | None): The path to save the output file.
        extra (ProcessingData | None): Additional processing data that may contain video stream information.
    Returns: The path to the newly created file with adjusted audio tempo.
    """
    if not input_path.is_file():
        raise ValueError(f"invalid {input_path=}")

    if from_rate is None:
        if extra and extra.video_stream and extra.video_stream.r_frame_rate:
            logger.info(f"inferred from_rate={extra.video_stream.r_frame_rate} from extra data")
            from_rate = float(extra.video_stream.r_frame_rate)
        elif has_video(input_path):
            stream = VideoStream.from_file(input_path)
            assert stream is not None, "has_video returned True, but no video stream found"
            if stream.r_frame_rate:
                logger.info(f"inferred from_rate={stream.r_frame_rate} from video stream")
                from_rate = float(stream.r_frame_rate)

    if from_rate is None:
        logger.warning("unable to infer from_rate from video stream")
        logger.info(f"using default from_rate={PAL_RATE}")
        from_rate = PAL_RATE

    return atempo_with(input_path, round(to_rate / from_rate, 8), output)


def atempo_with(
    input_path: Path,
    atempo_value: float,
    output: Path | None = None,
    extra: ProcessingData | None = None,
) -> Path:
    """
    Change the audio tempo of a multimedia file using FFmpeg's atempo filter.
    Args:
        input_path (Path): The path to the input multimedia file.
        atempo_value (float): The tempo adjustment value.
        output (Path | None): The path to save the output file.
        extra (ProcessingData | None): Additional processing data that may contain audio stream information.
    Returns: The path to the newly created file with adjusted audio tempo.
    """
    if not input_path.is_file():
        raise ValueError(f"invalid {input_path=}")
    if not has_audio(input_path):
        raise ValueError(f"input file {input_path} has no audio stream")

    stream = AudioStream.from_file(input_path)[extra.audio_track if extra else 0]
    suffix = f".{stream.format_names[0]}" if stream.format_names else input_path.suffix

    output = get_output_file_path(
        output or input_path.parent,
        default_name=f"{input_path.stem}_atempo_{atempo_value}{suffix}",
    )

    logger.info(f"adjusting audio tempo of {input_path.name} by atempo={atempo_value}\n\toutputing to {output}")
    command = ["-i", str(input_path), "-filter:a", f"atempo={atempo_value}", "-map_metadata", "0", str(output)]
    run_ffmpeg_command(command)
    return output


def atempo_video(
    input_path: Path,
    to_rate: float = NTSC_RATE,
    output: Path | None = None,
    extra: ProcessingData | None = None,
) -> Path:
    """
    Change the video tempo of a multimedia file using FFmpeg's setpts filter.
    Args:
        input_path (Path): The path to the input multimedia file.
        to_rate (float): The target frame rate to adjust the video tempo to. Default is NTSC_RATE (29.97).
        output (Path | None): The path to save the output file.
        extra (ProcessingData | None): Additional processing data that may contain video stream information.
    Returns: The path to the newly created file with adjusted video tempo.
    """
    if not input_path.is_file():
        raise ValueError(f"invalid {input_path=}")
    if not has_video(input_path):
        raise ValueError(f"input file {input_path} has no video stream")

    stream = extra.video_stream if extra and extra.video_stream else VideoStream.from_file(input_path)
    assert stream is not None, "has_video returned True, but no video stream found"
    suffix = f".{stream.format_names[0]}" if stream.format_names else input_path.suffix

    output = get_output_file_path(
        output or input_path.parent,
        default_name=f"{input_path.stem}_atempo_{1 / to_rate}{suffix}",
    )

    logger.info(f"adjusting video tempo of {input_path.name} to rate={to_rate}\n\toutputing to {output}")
    command = ["-i", str(input_path), "-r", f"{to_rate}", "-map_metadata", "0", str(output)]
    run_ffmpeg_command(command)
    return output
