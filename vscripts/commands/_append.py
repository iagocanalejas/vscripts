import logging
from pathlib import Path

from vscripts.data.models import ProcessingData
from vscripts.data.streams import AudioStream, SubtitleStream
from vscripts.utils import get_output_file_path, run_ffmpeg_command

logger = logging.getLogger("vscripts")


def append(
    attachment: Path,
    root: Path,
    output: Path | None = None,
    extra: ProcessingData | None = None,
) -> Path:
    """
    Append the contents of one multimedia file into another using FFmpeg and save the result as a new file.
    Args:
        attachment (Path): The path to the file that will be appended into another.
        root (Path): The path to the destination file into which 'attachment' will be appended.
        output (Path | None): The path to save the output file.
        extra (ProcessingData | None): Additional processing data that may contain audio stream information.
    Returns: The path to the newly created file that contains the appended content.
    """
    if not attachment.is_file() or not attachment.exists():
        raise ValueError(f"invalid {attachment=}")
    if not root.is_file() or not root.exists():
        raise ValueError(f"invalid {root=}")

    output = get_output_file_path(output or root.parent, f"{root.stem}_appended.mkv")
    if output.suffix.lower() != ".mkv":
        raise ValueError("output file must be an MKV file")

    logger.info(f"appending {attachment.name} into {root.name}\n\toutputting to {output}")
    command = ["-i", str(root), "-i", str(attachment), "-map", "0:v?"]

    # map all audio tracks except the one being appended
    for i in range(len(AudioStream.from_file(root))):
        if extra is not None and i == extra.audio_track:
            continue
        command += ["-map", f"0:a:{i}?"]

    command += [
        "-map",
        "1:a",
        "-map",
        "0:s?",
        "-map_metadata",
        "0",
        "-map_metadata",
        "1",
        "-c:v",
        "copy",
        "-c:a",
        "copy",
    ]

    # map and set metadata for subtitle streams
    for i, subs_stream in enumerate(SubtitleStream.from_file(root)):
        if subs_stream.codec_name in ["mov_text"]:
            command += [f"-c:s:{i}", "srt"]
        else:
            command += [f"-c:s:{i}", "copy"]

    command.append(str(output))
    run_ffmpeg_command(command)
    return output


def append_subs(attachment: Path, root: Path, lang: str | None = None, output: Path | None = None) -> Path:
    """
    Append subtitles to a video file using FFmpeg and save it as a new file.
    Args:
        attachment (Path): The path to the subtitle file to append.
        root (Path): The path to the input video file.
        lang (str | None): The language code for the subtitles.
        output (Path | None): The path to save the output file.
    Returns: The path to the newly created video file with subtitles.
    """
    if not attachment.is_file() or not attachment.exists():
        raise ValueError(f"invalid {attachment=}")
    if not root.is_file() or not root.exists():
        raise ValueError(f"invalid {root=}")

    output = get_output_file_path(output or root.parent, f"{root.stem}_subs{root.suffix}")

    logger.info(f"appending subtitles {attachment.name} into {root.name}\n\toutputting to {output}")
    command = [
        "-i",
        str(root),
        "-i",
        str(attachment),
        "-map",
        "0",
        "-map",
        "1",
        "-map_metadata",
        "0",
        "-map_metadata",
        "1",
        "-c",
        "copy",
    ]
    if lang:
        command += [
            f"-metadata:s:s:{len(SubtitleStream.from_file(root))}",
            f"language={lang}",
        ]
    if "mp4" in root.suffix:
        command += ["-scodec", "mov_text"]

    command.append(str(output))
    run_ffmpeg_command(command)
    return output
