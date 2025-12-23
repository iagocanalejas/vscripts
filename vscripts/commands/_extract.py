import logging
from pathlib import Path
from typing import Literal

from vscripts.constants import TYPE_TO_FFMPEG_TYPE
from vscripts.data.streams import AudioStream, SubtitleStream, VideoStream
from vscripts.utils import (
    ffmpeg_audio_codec_for_suffix,
    ffmpeg_subtitle_codec_for_suffix,
    get_output_file_path,
    run_ffmpeg_command,
    suffix_by_codec,
)

logger = logging.getLogger("vscripts")


def extract(
    input_path: Path,
    *,
    track: int | None = None,
    stream_type: Literal["audio", "subtitle"] = "audio",
    output: Path | None = None,
    **_,
) -> list[Path]:
    """Extract audio or subtitle streams from a media file.

    This function uses FFmpeg to extract one or more streams of the specified type from a media file and writes each
    extracted stream to a separate output file. When no track is specified, all streams of the requested type are
    extracted.

    The output file format is determined from the stream codec. Subtitle streams using SRT-compatible codecs are
    re-encoded to SRT; all other streams are copied without re-encoding.

    Args:
        input_path: Path to the input media file.
        track: Optional index of the stream to extract. If ``None``, all available streams of the given `stream_type`
            are extracted.
        stream_type: Type of stream to extract. Must be either ``"audio"`` or ``"subtitle"``.
        output: Optional output file path or directory. If not provided, extracted files are written to the input
            file’s directory.
        **_: Ignored keyword arguments (accepted for API compatibility).

    Returns:
        A list of paths to the extracted stream files. One path is returned per extracted stream.

    Raises:
        ValueError: If `input_path` does not exist or is not a file.
        ValueError: If `track` is out of range for the available streams of the specified `stream_type`.
    """
    if not input_path.is_file():
        raise ValueError(f"invalid {input_path=}")

    stream_list = AudioStream.from_file(input_path) if stream_type == "audio" else SubtitleStream.from_file(input_path)
    if track is not None and (track < 0 or track >= len(stream_list)):
        raise ValueError(f"invalid {stream_type} {track=} for {stream_list=}")

    def inner_extract(index: int) -> Path:
        stream = stream_list[index]
        suffix = suffix_by_codec(stream.codec_name, stream_type)
        final_path = get_output_file_path(
            output or input_path.parent,
            default_name=f"{input_path.stem}_{index}.{suffix}",
        )

        command = [
            "-i",
            str(stream.file_path),
            "-map",
            f"0:{TYPE_TO_FFMPEG_TYPE[stream_type]}:{index}",
            "-map_metadata",
            "0",
        ]

        if stream_type == "audio":
            command += ["-c:a", ffmpeg_audio_codec_for_suffix(input_path, final_path, stream.codec_name)]
        else:
            command += ["-c:s", ffmpeg_subtitle_codec_for_suffix(input_path, final_path, stream.codec_name)]

        command.append(str(final_path))

        logger.info(f"extracting {stream_type}={index} from {input_path.name}\n\toutputing to {final_path}")
        run_ffmpeg_command(command)
        return final_path

    indices = range(len(stream_list)) if track is None else [track]
    return [inner_extract(i) for i in indices]


def dissect(
    input_path: Path,
    *,
    skip_video: bool = False,
    output: Path | None = None,
    **_,
) -> list[Path]:
    """
    Dissect a media file into its constituent video, audio, and subtitle streams.

    This function extracts all video, audio, and subtitle streams from the specified media file and saves each stream
    as a separate file in the specified output directory. The output file format is determined based on the codec of
    each stream. Subtitle streams using SRT-compatible codecs are re-encoded to SRT; all other streams are copied
    without re-encoding.

    Args:
        input_path: Path to the input media file.
        skip_video: If ``True``, the video stream is not extracted. Defaults to ``False``.
        output: Optional output directory path. If not provided, the streams are saved in the same directory as the
            input file.
        **_: Ignored keyword arguments (accepted for API compatibility).

    Returns:
        A list of paths to the extracted stream files. One path is returned per extracted stream.

    Raises:
        ValueError: If `input_path` does not exist or is not a file.
        ValueError: If `output` is provided but is not a directory.
    """
    if not input_path.is_file():
        raise ValueError(f"invalid {input_path=}")

    output = output if output is not None else input_path.parent
    if not output.exists():
        output.mkdir(parents=True, exist_ok=True)
    if not output.is_dir():
        raise ValueError(f"invalid {output=}")

    output_paths = []
    video_stream = VideoStream.from_file(input_path)
    audio_streams = AudioStream.from_file(input_path)
    subtitle_streams = SubtitleStream.from_file(input_path)

    if video_stream is not None and not skip_video:
        video_path = output / f"stream_{video_stream.index:03d}.mkv"
        command = [
            "-i",
            str(input_path),
            "-map",
            "0:v:0",
            "-map_metadata",
            "0",
            "-c:v",
            "copy",
            str(video_path),
        ]

        logger.info(f"extracting video stream ({video_stream.codec_name})")
        run_ffmpeg_command(command)
        output_paths.append(video_path)

    logger.info(f"extracting {len(audio_streams)} audio streams")
    for a_stream in audio_streams:
        audio_path = output / f"stream_{a_stream.index:03d}.{suffix_by_codec(a_stream.codec_name, 'audio')}"
        command = [
            "-i",
            str(input_path),
            "-map",
            f"0:a:{a_stream.ffmpeg_index}",
            "-map_metadata",
            "0",
            "-c:a",
            ffmpeg_audio_codec_for_suffix(input_path, audio_path, a_stream.codec_name),
            str(audio_path),
        ]

        logger.info(f"\t- audio stream {a_stream.index} ({a_stream.codec_name})")
        run_ffmpeg_command(command)
        output_paths.append(audio_path)

    logger.info(f"extracting {len(subtitle_streams)} subtitle streams")
    for s_stream in subtitle_streams:
        subtitle_path = output / f"stream_{s_stream.index:03d}.{suffix_by_codec(s_stream.codec_name, 'subtitle')}"
        command = [
            "-i",
            str(input_path),
            "-map",
            f"0:s:{s_stream.ffmpeg_index}",
            "-map_metadata",
            "0",
            "-c:s",
            ffmpeg_subtitle_codec_for_suffix(input_path, subtitle_path, s_stream.codec_name),
        ]
        command.append(str(subtitle_path))

        logger.info(f"\t- subtitle stream {s_stream.index} ({s_stream.codec_name})")
        run_ffmpeg_command(command)
        output_paths.append(subtitle_path)

    return output_paths
