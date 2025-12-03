import logging
import statistics as stats
from pathlib import Path

from pyutils.paths import create_temp_dir
from vscripts.commands._extract import dissect
from vscripts.data.language import find_audio_language, find_subs_language
from vscripts.data.streams import AudioStream, FileStreams, SubtitleStream
from vscripts.utils import count_srt_entries, get_output_file_path, run_ffmpeg_command

logger = logging.getLogger("vscripts")


def merge(target: FileStreams, data: FileStreams, *, output: Path | None) -> FileStreams:
    """
    Merges audio and subtitle streams from `data` into the `target` video file.
    Args:
        target (FileStreams): The target FileStreams object containing the video stream.
        data (FileStreams): The data FileStreams object containing audio and subtitle streams to merge.
        output (Path | None): The output path for the merged file. If None, defaults to the target's parent directory.
    Returns: The FileStreams object representing the merged file.
    """

    if target.video is None:
        raise ValueError("no video stream found in target file")

    audios: list[AudioStream] = []
    subtitles: list[SubtitleStream] = []

    output = get_output_file_path(
        output or target.file_path.parent,
        default_name=f"{target.file_path.stem}_merged.mkv",
    )

    with create_temp_dir() as temp_dir:
        logger.info(f"using temporary directory {temp_dir}")
        target = dissect(target, output=Path(temp_dir) / target.file_path.stem)
        data = dissect(data, output=Path(temp_dir) / data.file_path.stem)
        assert target.video is not None, "video stream should not be None after dissecting"

        target_audios, target_subs = _retrieve_target_streams(target)
        data_audios, data_subs = _retrieve_data_streams(data)

        if len(data_audios) == 0:
            raise ValueError("no valid audio streams found in data file to merge")

        audios.extend(target_audios)
        audios.extend(data_audios)

        subtitles.extend(target_subs)
        subtitles.extend(data_subs)

        # check for forced subtitles in data, using duration of the first audio stream
        duration = float(data_audios[0].duration) if data_audios[0].duration else 0
        forced_subs = _retrieve_forced_subs(data, duration=duration)
        if forced_subs is not None:
            for sub in subtitles:
                if sub.file_path == forced_subs.file_path:
                    sub.default = True
                    break
            else:
                subtitles.append(forced_subs)

        command = ["-i", str(target.video.file_path)]

        for audio in audios:
            command += ["-i", str(audio.file_path)]

        for subtitle in subtitles:
            command += ["-i", str(subtitle.file_path)]

        command += ["-map", "0:v"]

        for i in range(len(audios)):
            command += ["-map", f"{i + 1}:a"]
            command += [f"-metadata:s:a:{i}", f"language={audios[i].language}"]

        for i in range(len(subtitles)):
            command += ["-map", f"{i + 1 + len(audios)}:s"]
            command += [f"-metadata:s:s:{i}", f"language={subtitles[i].language}"]
            if subtitles[i].default:
                command += [f"-disposition:s:{i}", "default"]

        command += ["-c:v", "copy", "-c:a", "copy", "-c:s", "copy"]
        command.append(str(output))

        logger.info(f"merging f{data} into {target}\n\toutputing to {output}")
        run_ffmpeg_command(command)

        new_streams = FileStreams(video=target.video, audios=audios, subtitles=subtitles)
        return new_streams.copy(with_new_path=output)


def _retrieve_target_streams(data: FileStreams) -> tuple[list[AudioStream], list[SubtitleStream]]:
    audio_streams: list[AudioStream] = []
    subtitle_streams: list[SubtitleStream] = []

    for audio_stream in data.audios:
        lang = find_audio_language(audio_stream)
        if lang in ["eng"]:
            logger.info(f"found audio {lang=} stream in target")
            audio_stream.language = lang
            audio_streams.append(audio_stream)
        if lang in ["spa", "glg"]:
            logger.warning(f"found audio {lang=} stream in target, skipping")

    for subtitle_stream in data.subtitles:
        lang = find_subs_language(subtitle_stream)
        if lang in ["eng", "spa", "glg"]:
            logger.info(f"found subtitle {lang=} stream in target")
            subtitle_stream.language = lang
            subtitle_streams.append(subtitle_stream)

    return audio_streams, subtitle_streams


def _retrieve_data_streams(data: FileStreams) -> tuple[list[AudioStream], list[SubtitleStream]]:
    audio_streams: list[AudioStream] = []
    subtitle_streams: list[SubtitleStream] = []

    for audio_stream in data.audios:
        lang = find_audio_language(audio_stream, force_detection=True)
        if lang in ["spa", "glg"]:
            logger.info(f"found audio {lang=} stream in data")
            audio_stream.language = lang
            audio_streams.append(audio_stream)

    for subtitle_stream in data.subtitles:
        lang = find_subs_language(subtitle_stream, force_detection=True)
        if lang in ["spa", "glg"]:
            logger.info(f"found subtitle {lang=} stream in data")
            subtitle_stream.language = lang
            subtitle_streams.append(subtitle_stream)

    if len([s for s in audio_streams if s.language == "spa"]) > 1:
        scored_streams = [(s, s.score) for s in audio_streams if s.language == "spa"]
        best_stream = max(scored_streams, key=lambda x: x[1])[0]
        logger.info("multiple spanish audio streams found, keeping only the best quality one")
        audio_streams = [s for s in audio_streams if s.file_path == best_stream.file_path or s.language != "spa"]

    return audio_streams, subtitle_streams


# TODO: improve language detection for forced subtitles
def _retrieve_forced_subs(data: FileStreams, duration: float) -> SubtitleStream | None:
    subtitles = data.subtitles
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
