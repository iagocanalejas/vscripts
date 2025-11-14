import logging
from pathlib import Path
from typing import Any

from vscripts.constants import UNKNOWN_LANGUAGE
from vscripts.data.language import ISO639_3_TO_1, find_language
from vscripts.data.models import ProcessingData
from vscripts.data.streams import AudioStream
from vscripts.utils import get_output_file_path, load_whisper, to_srt_timestamp

logger = logging.getLogger("vscripts")


def generate_subtitles(
    input_path: Path,
    output: Path | None = None,
    language: str | None = None,
    extra: ProcessingData | None = None,
) -> Path:
    """
    Generate subtitle file with specified language metadata using FFmpeg.
    Args:
        input_path (Path): The path to the input subtitle file.
        output (Path | None): The path to save the output subtitle file.
        language (str): The language code to set for the subtitle stream.
        extra (ProcessingData | None): Additional processing data.
    Returns: The path to the newly created subtitle file with updated language metadata.
    """
    if not input_path.is_file() or not input_path.exists():
        raise ValueError(f"invalid {input_path=}")

    if language is None:
        stream = AudioStream.from_file(input_path)[extra.audio_track if extra else 0]
        language = find_language(stream)
        logger.info(f"inferred language='{language}' for {input_path.name} from audio stream")

    if language == UNKNOWN_LANGUAGE:
        logger.warning(f"could not determine language for {input_path.name}, defaulting to 'eng'")
        language = "eng"

    if len(language) == 3:
        logger.info(f"converting ISO 639-3 language code '{language}' to ISO 639-1")
        language = ISO639_3_TO_1.get(language, language)

    output = get_output_file_path(
        output or input_path.parent,
        default_name=f"{input_path.stem}_{language}.srt",
    )

    # TODO: reel mode
    # TODO: translation mode
    model = load_whisper("turbo")
    logger.info(f"generating subtitles for {input_path.name} using language='{language}'")
    text = model.transcribe(str(input_path), language=language)

    segments: list[dict[str, Any]] = text.get("segments", [])  # type: ignore
    logger.info(f"found {len(segments)} segments in transcription for {input_path.name}")
    logger.debug(segments)
    _whisper_to_srt(segments, output)

    return output


def _whisper_to_srt(segments: list[dict[str, Any]], output: Path):
    with open(output, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, start=1):
            start = to_srt_timestamp(seg["start"])
            end = to_srt_timestamp(seg["end"])
            text = seg["text"].strip()

            f.write(f"{i}\n")
            f.write(f"{start} --> {end}\n")
            f.write(f"{text}\n\n")
