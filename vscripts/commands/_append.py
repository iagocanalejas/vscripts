import logging
from pathlib import Path

from pyutils.lists import flatten
from vscripts.data.streams import AudioStream, SubtitleStream
from vscripts.utils import get_output_file_path, run_ffmpeg_command
from vscripts.utils._utils import ffmpeg_audio_codec_for_suffix, ffmpeg_subtitle_codec_for_suffix

logger = logging.getLogger("vscripts")


def append(
    root: Path,
    attachment: Path,
    *,
    output: Path | None = None,
    **_,
) -> list[Path]:
    """Append audio and subtitle streams from one media file into another.

    This function merges the audio and subtitle streams of `attachment` into `root`, producing a new MKV file.
    Video streams from `root` are preserved without re-encoding. The output file must have an MKV extension, and
    streams are mapped appropriately with codec selection based on the output file format.

    Args:
        root: Path to the base media file to which streams will be appended.
        attachment: Path to the media file containing audio or subtitle streams to append.
        output: Optional output file path or directory. If not provided, a default file is created in the `root`
            directory with suffix `_appended.mkv`.
        **_: Ignored keyword arguments (accepted for API compatibility).

    Returns:
        A list containing a single Path to the output MKV file with the appended streams.

    Raises:
        ValueError: If `root` or `attachment` does not exist or is not a file.
        ValueError: If `attachment` contains no audio or subtitle streams.
        ValueError: If the output path does not have an MKV file extension.
    """
    if not root.is_file():
        raise ValueError(f"invalid {root=}")
    if not attachment.is_file():
        raise ValueError(f"invalid {attachment=}")

    audio_streams = AudioStream.from_file(root)
    subtitle_streams = SubtitleStream.from_file(root)

    new_audios = AudioStream.from_file(attachment)
    new_subs = SubtitleStream.from_file(attachment)
    if len(new_audios) == 0 and len(new_subs) == 0:
        raise ValueError(f"{attachment} contains no audio or subtitle streams to append")

    output = get_output_file_path(
        output or root.parent,
        default_name=f"{root.stem}_appended.mkv",
    )
    if "mkv" not in output.suffix.lower():
        raise ValueError("output file must be an MKV file")

    command = ["-i", str(root), "-i", str(attachment)]
    command += ["-map", "0:v?", "-c:v", "copy"]
    if len(audio_streams) > 0:
        command += ["-map", "0:a"]
        command += flatten(
            [f"-c:a:{i}", ffmpeg_audio_codec_for_suffix(root, output, s.codec_name)]
            for i, s in enumerate(audio_streams)
        )

    audio_idx = len(audio_streams)
    for a_stream in new_audios:
        logger.info(f"appending audio stream {a_stream.index} ({a_stream.codec_name}) from {attachment.name}")
        action = ffmpeg_audio_codec_for_suffix(attachment, output, a_stream.codec_name)
        command += ["-map", f"1:a:{a_stream.ffmpeg_index}", f"-c:a:{audio_idx}", action]
        audio_idx += 1

    if len(subtitle_streams) > 0:
        command += ["-map", "0:s"]
        command += flatten(
            [f"-c:s:{i}", ffmpeg_subtitle_codec_for_suffix(root, output, s.codec_name)]
            for i, s in enumerate(subtitle_streams)
        )

    sub_idx = len(subtitle_streams)
    for s_stream in new_subs:
        logger.info(f"appending subtitle stream {s_stream.index} ({s_stream.codec_name}) from {attachment.name}")
        action = ffmpeg_subtitle_codec_for_suffix(attachment, output, s_stream.codec_name)
        command += ["-map", f"1:s:{s_stream.ffmpeg_index}", f"-c:s:{sub_idx}", action]
        sub_idx += 1

    command += ["-map_metadata", "0"]
    command.append(str(output))

    # TODO: how do i handle metadata? add it here or spect an 'inspect' call later?
    logger.info(f"appending {attachment.name} into {root.name}\n\toutputing to {output}")
    run_ffmpeg_command(command)
    return [output]
