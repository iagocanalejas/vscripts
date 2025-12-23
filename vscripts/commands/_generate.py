import logging
from pathlib import Path
from typing import Any

from whisper import Whisper

from pyutils.paths import create_temp_dir
from vscripts.commands._extract import extract
from vscripts.constants import ISO639_3_TO_1, UNKNOWN_LANGUAGE
from vscripts.data.language import find_audio_language, is_unknown_language
from vscripts.data.streams import AudioStream
from vscripts.utils import get_output_file_path, load_whisper, to_srt_timestamp

logger = logging.getLogger("vscripts")


def generate_subtitles(
    input_path: Path,
    language: str | None = None,
    *,
    track: int | None = None,
    output: Path | None = None,
    **_,
) -> list[Path]:
    """
    Generate subtitle files from audio streams using speech-to-text.

    This function transcribes one or more audio streams from a media file into subtitle files using a Whisper speech
    recognition model. If no language is explicitly provided, the language is inferred from the audio stream when
    possible.

    When multiple audio streams are present and language inference is required, non-primary streams may be temporarily
    extracted to enable accurate language detection.

    Args:
        input_path: Path to the input media file.
        language: Optional language code to use for transcription. If provided, it must be a valid ISO 639-3 code.
            When omitted or unknown, the language is inferred from the audio stream.
        track: Optional index of the audio track to transcribe. If ``None``, all available audio tracks are processed.
        output: Optional output file path or directory. If not provided, subtitle files are written to the input
            file’s directory.
        **_: Ignored keyword arguments (accepted for API compatibility).

    Returns:
        A list of paths to the generated subtitle (`.srt`) files. One path is returned per processed audio stream.

    Raises:
        ValueError: If `input_path` does not exist or is not a file.
        ValueError: If no audio streams are found in the input file.
        ValueError: If `track` is out of range for the available audio streams.
        ValueError: If `language` is provided and is not a valid ISO 639-3 language code.
    """
    if not input_path.is_file():
        raise ValueError(f"invalid {input_path=}")

    streams = AudioStream.from_file(input_path)
    if len(streams) == 0:
        raise ValueError(f"no audio streams found in {input_path=}")
    if track is not None and (track < 0 or track >= len(streams)):
        raise ValueError(f"invalid audio {track=} for {streams=}")
    if language is not None and len(language) != 3:
        raise ValueError(f"invalid language code '{language}', must be ISO 639-3")

    model = load_whisper("medium")

    def inner_generate(index: int, lang: str | None) -> Path:
        stream = streams[index]

        if index > 0:
            extracted = extract(input_path, track=index, stream_type="audio", output=Path(temp_dir))[0]
            stream = AudioStream.from_file(extracted)[0]

        if lang is None or is_unknown_language(lang):
            lang = find_audio_language(stream)
            logger.info(f"inferred {lang=} for audio={stream.ffmpeg_index} in {input_path.name}")

        if lang == UNKNOWN_LANGUAGE:  # pragma: no cover
            logger.warning(f"could not determine language for audio={stream.ffmpeg_index}, defaulting to 'eng'")
            lang = "eng"

        if len(lang) == 3:
            logger.debug(f"converting ISO 639-3 language code {lang=} to ISO 639-1")
            lang = ISO639_3_TO_1.get(lang, lang)

        output_path = get_output_file_path(
            output or input_path.parent,
            default_name=f"{stream.file_path.stem}_{lang}.srt",
        )

        logger.info(f"generating subtitles for audio={stream.ffmpeg_index} in {stream.file_path.name} using {lang=}")
        content = _transcribe(model, stream, language=lang)
        with output_path.open("w", encoding="utf-8") as f:
            f.write(content)

        return output_path

    with create_temp_dir() as temp_dir:
        indices = range(len(streams)) if track is None else [track]
        return [inner_generate(i, lang=language) for i in indices]


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
