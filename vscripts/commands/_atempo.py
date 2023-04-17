import logging
from pathlib import Path

from vscripts.commands._utils import get_output_file_path, run_ffmpeg_command
from vscripts.constants import NTSC_RATE, PAL_RATE
from vscripts.data.streams import VideoStream

logger = logging.getLogger("vscripts")


def atempo(
    input_path: Path,
    from_rate: float | None = None,
    to_rate: float = NTSC_RATE,
    output: Path | None = None,
) -> Path:
    """
    Change the audio tempo of a multimedia file using FFmpeg's atempo filter.
    Args:
        input_path (Path): The path to the input multimedia file.
        from_rate (float | None): The original frame rate of the video or inferred from the video stream.
        to_rate (float): The target frame rate to adjust the audio tempo to. Default is NTSC_RATE (29.97).
        output (Path | None): The path to save the output file.
    Returns: The path to the newly created file with adjusted audio tempo.
    """
    if not input_path.is_file() or not input_path.exists():
        raise ValueError(f"invalid {input_path=}")

    if from_rate is None:
        stream = VideoStream.from_file(input_path)
        if stream is not None and stream.r_frame_rate:
            logger.info(f"inferred from_rate={stream.r_frame_rate} from video stream")
            from_rate = float(stream.r_frame_rate)
    if from_rate is None:
        logger.warning("unable to infer from_rate from video stream")
        logger.info(f"using default from_rate={PAL_RATE}")
        from_rate = PAL_RATE

    return atempo_with(input_path, round(to_rate / from_rate, 8), output)


def atempo_with(input_path: Path, atempo_value: float, output: Path | None = None) -> Path:
    """
    Change the audio tempo of a multimedia file using FFmpeg's atempo filter.
    Args:
        input_path (Path): The path to the input multimedia file.
        atempo_value (float): The tempo adjustment value.
        output (Path | None): The path to save the output file.
    Returns: The path to the newly created file with adjusted audio tempo.
    """
    if not input_path.is_file() or not input_path.exists():
        raise ValueError(f"invalid {input_path=}")

    # TODO: instead of input_path.suffix, we need to parse the audio stream codec to determine the correct output format

    output = get_output_file_path(
        output or input_path.parent,
        default_name=f"{input_path.stem}_atempo_{atempo_value}{input_path.suffix}",
    )

    logger.info(f"adjusting audio tempo of {input_path} by atempo={atempo_value}, outputting to {output}")
    command = ["ffmpeg", "-i", str(input_path), "-filter:a", f"atempo={atempo_value}", "-vn", str(output)]
    logger.info(command)

    run_ffmpeg_command(command)
    return output


def atempo_video(input_path: Path, to_rate: float = NTSC_RATE, output: Path | None = None) -> Path:
    """
    Change the video tempo of a multimedia file using FFmpeg's setpts filter.
    Args:
        input_path (Path): The path to the input multimedia file.
        to_rate (float): The target frame rate to adjust the video tempo to. Default is NTSC_RATE (29.97).
        output (Path | None): The path to save the output file.
    Returns: The path to the newly created file with adjusted video tempo.
    """
    if not input_path.is_file() or not input_path.exists():
        raise ValueError(f"invalid {input_path=}")

    output = get_output_file_path(
        output or input_path.parent,
        default_name=f"{input_path.stem}_atempo_{1 / to_rate}{input_path.suffix}",
    )

    logger.info(f"adjusting video tempo of {input_path} to rate={to_rate}, outputting to {output}")
    command = ["ffmpeg", "-i", str(input_path), "-r", f"{to_rate}", str(output)]
    logger.info("Running command: %s", " ".join(command))

    run_ffmpeg_command(command)
    return output
