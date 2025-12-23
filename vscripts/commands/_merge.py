import logging
import statistics as stats
from pathlib import Path

from pyutils.paths import create_temp_dir
from vscripts.commands._extract import dissect
from vscripts.data.language import find_audio_language, find_subs_language
from vscripts.data.streams import AudioStream, SubtitleStream, VideoStream
from vscripts.utils import count_srt_entries, get_output_file_path, infer_media_type, is_subs, run_ffmpeg_command

logger = logging.getLogger("vscripts")


def merge(
    target: Path,
    data: Path,
    *,
    output: Path | None,
    **_,
) -> list[Path]:
    """Merge audio and subtitle streams from a data file into a target video.

    This function combines the video stream from `target` with audio and subtitle streams from both `target` and
    `data`. The resulting file preserves the original video without re-encoding and copies all audio and subtitle
    streams. Forced subtitles in the data file are automatically set as default if applicable.

    Args:
        target: Path to the base video file whose video stream will be used.
        data: Path to the media file containing audio and subtitle streams to merge into the target.
        output: Optional output file path. If not provided, a default path is created in the target file’s directory
            with suffix `_merged.mkv`.
        **_: Ignored keyword arguments (accepted for API compatibility).

    Returns:
        Path to the merged output MKV file.

    Raises:
        ValueError: If `data` contains no valid audio streams to merge.
        ValueError: If `target` or `data` does not exist or is not a file.
    """
    if not target.is_file():
        raise ValueError(f"invalid {target=}")
    if not data.is_file():
        raise ValueError(f"invalid {data=}")

    video: VideoStream | None = None
    audios: list[AudioStream] = []
    subtitles: list[SubtitleStream] = []

    output = get_output_file_path(
        output or target.parent,
        default_name=f"{target.stem}_merged.mkv",
    )

    with create_temp_dir() as temp_dir:
        logger.info(f"using temporary directory {temp_dir}")
        target_path = dissect(target, output=Path(temp_dir) / target.stem)
        data_path = dissect(data, output=Path(temp_dir) / data.stem)

        video, target_audios, target_subs = _retrieve_target_streams(target_path)
        data_audios, data_subs = _retrieve_data_streams(data_path)

        if len(data_audios) == 0:
            raise ValueError("no valid audio streams found in data file to merge")

        audios.extend(target_audios)
        audios.extend(data_audios)

        subtitles.extend(target_subs)
        subtitles.extend(data_subs)

        # check for forced subtitles in data, using duration of the first audio stream
        duration = float(data_audios[0].duration) if data_audios[0].duration else 0
        forced_subs = _retrieve_forced_subs(data_path, duration=duration)
        if forced_subs is not None:
            for sub in subtitles:
                if sub.file_path == forced_subs.file_path:
                    sub.default = True
                    break
            else:
                subtitles.append(forced_subs)

        command = ["-i", str(video.file_path)]

        for audio in audios:
            command += ["-i", str(audio.file_path)]

        for subtitle in subtitles:
            command += ["-i", str(subtitle.file_path)]

        command += ["-map", "0:v"]

        for i in range(len(audios)):
            command += ["-map", f"{i + 1}:a"]
            lang = audios[i].language
            command += [f"-metadata:s:a:{i}", f"language={lang}"]

        for i in range(len(subtitles)):
            command += ["-map", f"{i + 1 + len(audios)}:s"]
            lang = subtitles[i].language
            command += [f"-metadata:s:s:{i}", f"language={lang}"]
            if subtitles[i].default:
                command += [f"-disposition:s:{i}", "default"]

        command += ["-c:v", "copy", "-c:a", "copy", "-c:s", "copy"]
        command.append(str(output))

        logger.info(f"merging f{data} into {target}\n\toutputing to {output}")
        run_ffmpeg_command(command)
        return [output]


def _retrieve_target_streams(target_paths: list[Path]) -> tuple[VideoStream, list[AudioStream], list[SubtitleStream]]:
    video_stream: VideoStream | None = None
    audio_streams: list[AudioStream] = []
    subtitle_streams: list[SubtitleStream] = []

    for file in target_paths:
        if not file.is_file():
            logger.warning(f"skipping non-file {file} in dissected target path (should not happen)")
            continue

        ext = infer_media_type(file)
        if ext == "video":
            logger.info(f"using video stream in target file: {file}")
            video_stream = VideoStream.from_file(file)
            continue
        elif ext == "audio":
            audio_stream = AudioStream.from_file(file)[0]
            lang = find_audio_language(audio_stream)
            if lang in ["eng"]:
                logger.info(f"found audio {lang=} stream in target")
                audio_stream.language = lang
                audio_streams.append(audio_stream)
            if lang in ["spa", "glg"]:
                logger.warning(f"found audio {lang=} stream in target, skipping")
            continue
        elif ext == "subtitle":
            subtitle_stream = SubtitleStream.from_file(file)[0]
            lang = find_subs_language(subtitle_stream)
            if lang in ["eng", "spa", "glg"]:
                logger.info(f"found subtitle {lang=} stream in target")
                subtitle_stream.language = lang
                subtitle_streams.append(subtitle_stream)
            continue
        else:
            logger.warning(f"skipping {ext} stream in {file}")
            continue

    if video_stream is None:
        raise ValueError("no video stream found in target file")
    return video_stream, audio_streams, subtitle_streams


def _retrieve_data_streams(data_paths: list[Path]) -> tuple[list[AudioStream], list[SubtitleStream]]:
    audio_streams: list[AudioStream] = []
    subtitle_streams: list[SubtitleStream] = []

    for file in data_paths:
        if not file.is_file():
            logger.warning(f"skipping non-file {file} in dissected data file (should not happen)")
            continue

        # TODO: CAP S02E03 not finding spanish audio track
        ext = infer_media_type(file)
        if ext == "audio":
            audio_stream = AudioStream.from_file(file)[0]
            lang = find_audio_language(audio_stream, force_detection=True)
            if lang in ["spa", "glg"]:
                logger.info(f"found audio {lang=} stream in data")
                audio_stream.language = lang
                audio_streams.append(audio_stream)
            continue
        elif ext == "subtitle":
            subtitle_stream = SubtitleStream.from_file(file)[0]
            lang = find_subs_language(subtitle_stream, force_detection=True)
            if lang in ["spa", "glg"]:
                logger.info(f"found subtitle {lang=} stream in data")
                subtitle_stream.language = lang
                subtitle_streams.append(subtitle_stream)
            continue
        else:
            logger.warning(f"skipping {ext} stream in {file}")
            continue

    if len([s for s in audio_streams if s.language == "spa"]) > 1:
        scored_streams = [(s, s.score) for s in audio_streams if s.language == "spa"]
        best_stream = max(scored_streams, key=lambda x: x[1])[0]
        logger.info("multiple spanish audio streams found, keeping only the best quality one")
        audio_streams = [s for s in audio_streams if s.file_path == best_stream.file_path or s.language != "spa"]

    return audio_streams, subtitle_streams


# TODO: improve language detection for forced subtitles
def _retrieve_forced_subs(data_paths: list[Path], duration: float) -> SubtitleStream | None:
    subtitles = [SubtitleStream.from_file(f)[0] for f in data_paths if is_subs(f)]
    counts = [(count_srt_entries(s.file_path.read_text(encoding="utf-8", errors="ignore")), s) for s in subtitles]
    if len(counts) == 0:
        return None

    if len(subtitles) == 1:
        if counts[0][0] <= duration / 60:  # less than 1 subtitle per minute
            logger.info("only one subtitle stream found, assuming it's a forced subtitle stream")
            subtitles[0].default = True
            subtitles[0].language = "spa"
            return subtitles[0]
        return None

    min_count = min([count for count, _ in counts])
    if min_count < (5 * stats.mean([count for count, _ in counts if count > min_count])):
        subs = next((stream for count, stream in counts if count <= min_count), None)
        assert subs is not None, "subtitle stream should not be None here"
        logger.info("found a subtitle stream with very few entries, assuming it's a forced subtitle stream")

        subs.default = True
        subs.language = "spa"
        return subs
    return None
