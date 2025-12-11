import logging
from pathlib import Path

from vscripts.constants import NTSC_RATE, PAL_RATE
from vscripts.data.streams import AudioStream, FileStreams
from vscripts.utils import get_output_file_path, run_ffmpeg_command

logger = logging.getLogger("vscripts")


def atempo(
    streams: FileStreams,
    from_rate: float | None = None,
    to_rate: float = NTSC_RATE,
    *,
    track: int | None = None,
    output: Path | None = None,
    **_,
) -> FileStreams:
    """
    Change the audio tempo of a multimedia file using FFmpeg's atempo filter.
    Args:
        streams (FileStreams): The FileStreams object representing the multimedia file to be processed.
        from_rate (float | None): The original frame rate of the video or inferred from the video stream.
        to_rate (float): The target frame rate to adjust the audio tempo to. Default is NTSC_RATE (29.97).
        track (int | None): The index of the audio track to adjust. None will apply the adjustment to all audio streams.
        output (Path | None): The path to save the output file.
    Returns: The FileStreams object with updated file path.
    """
    if from_rate is None:
        if streams.video and streams.video.r_frame_rate:
            logger.info(f"inferred from_rate={streams.video.r_frame_rate} from extra data")
            from_rate = float(streams.video.r_frame_rate)

    if from_rate is None:
        logger.warning("unable to infer from_rate from video stream")
        logger.info(f"using default from_rate={PAL_RATE}")
        from_rate = PAL_RATE

    return atempo_with(streams, round(to_rate / from_rate, 8), track=track, output=output)


def atempo_with(
    streams: FileStreams,
    atempo_value: float,
    *,
    track: int | None = None,
    output: Path | None = None,
    **_,
) -> FileStreams:
    """
    Change the audio tempo of a multimedia file using FFmpeg's atempo filter.
    Args:
        streams (FileStreams): The FileStreams object representing the multimedia file to be processed.
        atempo_value (float): The tempo adjustment value.
        track (int | None): The index of the audio track to adjust. None will apply the adjustment to all audio streams.
        output (Path | None): The path to save the output file.
    Returns: The FileStreams object with updated file path.
    """
    if len(streams.audios) < 1:
        raise ValueError(f"no audio streams found in {streams.file_path=}, cannot adjust tempo")
    if atempo_value < 0:
        raise ValueError(f"invalid atempo value {atempo_value=}, must be non-negative")
    if track is not None and (track < 0 or track >= len(streams.audios)):
        raise ValueError(f"invalid audio {track=} for {streams.audios=}")
    if track is not None and not streams.audios[track].file_path.is_file():
        raise ValueError(f"invalid {streams.audios[track].file_path=}")
    if track is None and any(not a.file_path.is_file() for a in streams.audios):
        raise ValueError(f"one or more audio stream file paths are invalid in {streams.audios=}")

    output = get_output_file_path(
        output or streams.file_path.parent,
        default_name=f"{streams.file_path.stem}_atempo_{atempo_value}{streams.file_path.suffix}",
    )

    logger.info(f"adjusting audio tempo of {streams.file_path.name} by atempo={atempo_value}\n\toutputing to {output}")
    command = ["-i", str(streams.file_path)]

    indices = range(len(streams.audios)) if track is None else [track]
    for i in indices:
        command += [f"-filter:a:{i}", f"atempo={atempo_value}"]
        streams.audios[i].ffmpeg_index = 0
        streams.audios[i].file_path = output
        _update_duration(streams.audios[i], atempo_value)

    command += ["-map_metadata", "0", str(output)]

    run_ffmpeg_command(command)
    return streams


def atempo_video(
    streams: FileStreams,
    to_rate: float = NTSC_RATE,
    *,
    output: Path | None = None,
) -> FileStreams:
    """
    Change the video tempo of a multimedia file using FFmpeg's setpts filter.
    Args:
        streams (FileStreams): The FileStreams object representing the multimedia file to be processed.
        to_rate (float): The target frame rate to adjust the video tempo to. Default is NTSC_RATE (29.97).
        output (Path | None): The path to save the output file.
    Returns: The FileStreams object with updated file path.
    """
    if streams.video is None:
        raise ValueError(f"no video streams found in {streams.file_path=}, cannot adjust video tempo")
    if not streams.video.file_path.is_file():
        raise ValueError(f"invalid {streams.file_path=}")
    if to_rate < 0:
        raise ValueError(f"invalid to_rate {to_rate=}, must be non-negative")

    suffix = f".{streams.video.format_names[0]}" if streams.video.format_names else streams.video.file_path.suffix

    output = get_output_file_path(
        output or streams.file_path.parent,
        default_name=f"{streams.file_path.stem}_atempo_{1 / to_rate}{suffix}",
    )

    logger.info(f"adjusting video tempo of {streams.file_path.name} to rate={to_rate}\n\toutputing to {output}")
    command = ["-i", str(streams.file_path), "-r", f"{to_rate}", "-map_metadata", "0", str(output)]
    run_ffmpeg_command(command)
    streams.video.file_path = output
    return streams


def _update_duration(stream: AudioStream, atempo: float) -> None:
    if stream.duration is not None:
        stream.duration = stream.duration / atempo
