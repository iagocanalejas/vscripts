import logging
import subprocess
from pathlib import Path

from vscripts.commands._utils import get_output_file_path, run_ffmpeg_command
from vscripts.constants import ENCODING_PRESETS, EncodingPreset

logger = logging.getLogger("vscripts")


def delay(input_path: Path, delay: float, output: Path | None = None) -> Path:
    """
    Apply an audio delay effect to a multimedia file using FFmpeg and save it as a new file.
    Args:
        input_path (Path): The path to the audio or video file to be processed.
        delay(float): The delay time in seconds.
        output (Path | None): The path to save the output file.
    Returns: The path to the newly created file with the audio delay effect applied.
    """
    if not input_path.is_file() or not input_path.exists():
        raise ValueError(f"invalid {input_path=}")

    output = get_output_file_path(
        output or input_path.parent,
        default_name=f"{input_path.stem}_delayed_{delay}{input_path.suffix}",
    )

    logger.info(f"applying audio delay of {delay}ms to {input_path}, outputting to {output}")
    command = [
        "ffmpeg",
        "-i",
        str(input_path),
        "-af",
        f"adelay={int(float(delay) * 1000)}:all=true",
        "-strict",
        "experimental",
        str(output),
    ]
    logger.info(command)

    run_ffmpeg_command(command)
    return output


def hasten(input_path: Path, hasten_factor: float, output: Path | None = None) -> Path:
    """
    Adjust the playback speed of a multimedia file using FFmpeg and save it as a new file.
    Args:
        input_path (Path): The path to the input audio or video file to adjust.
        hasten_factor (float): The hasten factor to adjust playback speed.
        output (Path | None): The path to save the output file.
    Returns: The path to the newly created hastened audio or video file.
    """
    if not input_path.is_file() or not input_path.exists():
        raise ValueError(f"invalid {input_path=}")

    output = get_output_file_path(
        output or input_path.parent,
        default_name=f"{input_path.stem}_hastened_{hasten_factor}{input_path.suffix}",
    )

    logger.info(f"adjusting playback speed of {input_path} by hasten={hasten_factor}, outputting to {output}")
    command = [
        "ffmpeg",
        "-i",
        str(input_path),
        "-ss",
        f"{hasten_factor}",
        "-acodec",
        "copy",
        "-strict",
        "experimental",
        str(output),
    ]
    logger.info(command)

    run_ffmpeg_command(command)
    return output


def reencode(input_path: Path, quality: EncodingPreset, output: Path | None = None) -> Path:
    """
    Re-encode a multimedia file using HandBrakeCLI with a specified quality preset and save it as a new file.
    Args:
        input_path (Path): The path to the input multimedia file.
        quality (EncodingPreset): The quality preset to use for re-encoding.
        output (Path | None): The path to save the output file.
    Returns: The path to the newly created re-encoded multimedia file.
    """
    if not input_path.is_file() or not input_path.exists():
        raise ValueError(f"invalid {input_path=}")

    output = get_output_file_path(
        output or input_path.parent,
        default_name=f"{input_path.stem}_{quality}{input_path.suffix}",
    )

    logger.info(f"re-encoding {input_path} with quality={quality}, outputting to {output}")
    command = [
        "HandBrakeCLI",
        f"--preset={ENCODING_PRESETS[quality]}",
        "-i",
        str(input_path),
        "-o",
        str(output),
        "--format=mkv",
        "--all-audio",
        "--audio-copy-mask=ac3,dts,dtshd,eac3,truehd",
        "--audio-fallback=ac3",
        "--all-subtitles",
        "--subtitle-burn=none",
    ]
    logger.info(command)

    # TODO: create something like run_handbrake_command(command)
    subprocess.run(command, text=True)
    return output
