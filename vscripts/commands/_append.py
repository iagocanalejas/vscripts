import logging
from pathlib import Path

from vscripts.commands._utils import get_output_file_path, run_ffmpeg_command
from vscripts.data.language import find_subs_language
from vscripts.data.streams import SubtitleStream

logger = logging.getLogger("vscripts")


def append(attachment: Path, root: Path, output: Path | None = None) -> Path:
    """
    Append the contents of one multimedia file into another using FFmpeg and save the result as a new file.
    Args:
        attachment (Path): The path to the file that will be appended into another.
        root (Path): The path to the destination file into which 'attachment' will be appended.
        output (Path | None): The path to save the output file.
    Returns: The path to the newly created file that contains the appended content.
    """
    if not attachment.is_file() or not attachment.exists():
        raise ValueError(f"invalid {attachment=}")
    if not root.is_file() or not root.exists():
        raise ValueError(f"invalid {root=}")

    output = get_output_file_path(output or root.parent, f"{root.stem}_appended.mkv")
    if output.suffix.lower() != ".mkv":
        raise ValueError("output file must be an MKV file")

    logger.info(f"appending {attachment} into {root}, outputting to {output}")
    command = ["ffmpeg", "-i", str(root), "-i", str(attachment), "-map", "0", "-map", "1", "-c", "copy", str(output)]
    logger.info(command)

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

    if not lang:
        lang = find_subs_language(SubtitleStream.from_file(attachment)[0])
        print(lang)

    logger.info(f"appending subtitles {attachment} into {root}, outputting to {output}")
    command = [
        "ffmpeg",
        "-i",
        str(root),
        "-i",
        str(attachment),
        "-map",
        "0",
        "-map",
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
    logger.info(command)

    run_ffmpeg_command(command)
    return output
