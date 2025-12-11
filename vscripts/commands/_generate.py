import logging
from pathlib import Path
from typing import Any

from whisper import Whisper

from pyutils.paths import create_temp_dir
from vscripts.commands._extract import extract
from vscripts.constants import ISO639_1_TO_3, ISO639_3_TO_1, UNKNOWN_LANGUAGE
from vscripts.data.language import find_audio_language
from vscripts.data.streams import AudioStream, FileStreams, SubtitleStream
from vscripts.utils import get_output_file_path, load_whisper, to_srt_timestamp

logger = logging.getLogger("vscripts")


def generate_subtitles(
    streams: FileStreams,
    language: str | None = None,
    *,
    track: int | None = None,
    output: Path | None = None,
    **_,
) -> FileStreams:
    """
    Generate subtitles for a multimedia file using OpenAI's Whisper model.
    Args:
        streams (FileStreams): The FileStreams object representing the multimedia file to be processed.
        language (str): The language code to set for the subtitle stream.
        track (int | None): The index of the audio track to use for language inference. None will use all audio streams.
        output (Path | None): The path to save the output subtitle file.
    Returns: The FileStreams object with the new added subtitle streams.
    """
    if len(streams.audios) < 1:
        raise ValueError(f"no audio streams found in {streams.file_path=}, cannot generate")
    if track is not None and (track < 0 or track >= len(streams.audios)):
        raise ValueError(f"invalid audio {track=} for {streams.audios=}")
    if track is not None and not streams.audios[track].file_path.is_file():
        raise ValueError(f"invalid {streams.audios[track].file_path=}")
    if track is None and any(not a.file_path.is_file() for a in streams.audios):
        raise ValueError(f"one or more audio stream file paths are invalid in {streams.audios=}")
    if language is not None and len(language) != 3:
        raise ValueError(f"invalid language code '{language}', must be ISO 639-3")

    model = load_whisper("medium")

    def inner_generate(index: int, lang: str | None) -> None:
        stream = streams.audios[index]
        og_stream: AudioStream | None = None

        output_path = get_output_file_path(
            output or stream.file_path.parent,
            default_name=f"{stream.file_path.stem}_{lang}.srt",
        )

        file_streams = [a for a in streams.audios if a.file_path == stream.file_path]
        if len(file_streams) > 1:
            logger.info(f"multiple audios found in {stream.file_path.name}, extracting stream={stream.ffmpeg_index}")
            og_stream = stream.copy()
            extract(streams, track=file_streams.index(stream), stream_type="audio", output=Path(temp_dir))

        if lang is None:
            lang = find_audio_language(stream)
            logger.info(f"inferred {lang=} for audio={stream.ffmpeg_index} in {stream.file_path.name}")

        if lang == UNKNOWN_LANGUAGE:  # pragma: no cover
            logger.warning(f"could not determine language for audio={stream.ffmpeg_index}, defaulting to 'eng'")
            lang = "eng"

        if len(lang) == 3:
            logger.debug(f"converting ISO 639-3 language code {lang=} to ISO 639-1")
            lang = ISO639_3_TO_1.get(lang, lang)

        logger.info(f"generating subtitles for audio={stream.ffmpeg_index} in {stream.file_path.name} using {lang=}")
        content = _transcribe(model, stream, language=lang)
        with output_path.open("w", encoding="utf-8") as f:
            f.write(content)

        new_stream = SubtitleStream(
            _index=0,
            ffmpeg_index=0,
            codec_name="mov_text",
            codec_type="subtitle",
            language=ISO639_1_TO_3.get(lang, lang),
            generated=True,
        )
        new_stream.file_path = output_path
        streams.subtitles.append(new_stream)
        if og_stream is not None:  # reset original stream if it was altered during extraction
            streams.audios[index] = og_stream

    with create_temp_dir() as temp_dir:
        indices = range(len(streams.audios)) if track is None else [track]
        for i in indices:
            inner_generate(i, lang=language)

    return streams


def _transcribe(model: Whisper, stream: AudioStream, language: str) -> str:
    transcription = model.transcribe(str(stream.file_path), language=language)
    segments: list[dict[str, Any]] = transcription.get("segments", [])  # type: ignore

    content = ""
    for i, seg in enumerate(segments, start=1):
        start = to_srt_timestamp(seg["start"])
        end = to_srt_timestamp(seg["end"])
        text = seg["text"].strip()

        content += f"{i}\n{start} --> {end}\n{text}\n\n"

    return content
