import asyncio
import logging
from pathlib import Path
from typing import Literal

from googletrans import Translator
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from pyutils.paths import create_temp_dir
from vscripts.commands._extract import extract
from vscripts.constants import INVISIBLE_SEPARATOR, ISO639_3_TO_1, UNKNOWN_LANGUAGE
from vscripts.data.language import find_subs_language
from vscripts.data.streams import SubtitleStream
from vscripts.utils import get_output_file_path, parse_srt, rebuild_srt

logger = logging.getLogger("vscripts")


def translate_subtitles(
    input_path: Path,
    to_language: str,
    from_language: str | None = None,
    *,
    track: int | None = None,
    mode: Literal["local", "google"] = "local",
    output: Path | None = None,
    **_,
) -> list[Path]:
    """
    Translate subtitle files from one language to another.

    This function translates one or more subtitle streams from a media file into a specified target language. If no
    track is specified, all available subtitle streams are processed. The source language can be explicitly provided
    or inferred from the subtitle stream when possible.

    Args:
        input_path: Path to the input media file containing subtitle streams.
        to_language: Target language code for translation. Must be a valid ISO 639-3 code.
        from_language: Optional source language code. If provided, it must be a valid ISO 639-3 code. When omitted,
            the source language is inferred from the subtitle stream.
        track: Optional index of the subtitle track to translate. If ``None``, all available subtitle tracks are
            processed.
        mode: Translation mode to use. Must be either ``"local"`` or ``"google"``.
        output: Optional output file path or directory. If not provided, translated subtitle files are written to the
            input file’s directory.
        **_: Ignored keyword arguments (accepted for API compatibility).

    Returns:
        A list of paths to the translated subtitle (`.srt`) files. One path is returned per processed subtitle stream.

    Raises:
        ValueError: If `input_path` does not exist or is not a file.
        ValueError: If no subtitle streams are found in the input file.
        ValueError: If `track` is out of range for the available subtitle streams.
        ValueError: If `to_language` is not a valid ISO 639-3 language code.
        ValueError: If `from_language` is provided and is not a valid ISO
    """
    if not input_path.is_file():
        raise ValueError(f"invalid {input_path=}")

    streams = SubtitleStream.from_file(input_path)
    if len(streams) == 0:
        raise ValueError(f"no subtitle streams found in {input_path=}")
    if track is not None and (track < 0 or track >= len(streams)):
        raise ValueError(f"invalid subtitle track index {track=} for {streams=}")
    if len(to_language) != 3:
        raise ValueError(f"invalid target language code '{to_language}', must be ISO 639-3")
    if from_language is not None and len(from_language) != 3:
        raise ValueError(f"invalid source language code '{from_language}', must be ISO 639-3")

    def inner_translate(index: int, to_lang: str, from_lang: str | None) -> Path:
        stream = streams[index]
        if index > 0:
            extracted = extract(input_path, track=index, stream_type="subtitle", output=Path(temp_dir))[0]
            stream = SubtitleStream.from_file(extracted)[0]

        output_path = get_output_file_path(
            output or input_path.parent,
            default_name=f"{input_path.stem}_track{index}_{to_lang}.srt",
        )

        if from_lang is None:
            from_lang = find_subs_language(stream)
            logger.info(f"inferred '{from_lang}' for {input_path.name} from audio stream")

        if from_lang == UNKNOWN_LANGUAGE:
            logger.warning(f"could not determine language for {input_path.name}, defaulting to 'eng'")
            from_lang = "eng"

        if len(from_lang) == 3:
            logger.debug(f"converting ISO 639-3 from_lang code '{from_lang=}' to ISO 639-1")
            from_lang = ISO639_3_TO_1.get(from_lang, from_lang)
        if len(to_lang) == 3:
            logger.debug(f"converting ISO 639-3 lang code '{to_lang=}' to ISO 639-1")
            to_lang = ISO639_3_TO_1.get(to_lang, to_lang)

        with stream.file_path.open("r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        logger.info(f"translating subtitles from '{from_lang=}' to '{to_lang=}'. {mode=}")
        if mode == "google":
            content = _translate_subtitles_googletrans(content, from_lang, to_lang)
        else:
            content = _translate_subtitles_helsinki(content, from_lang, to_lang)

        logger.info(f"writing translated subtitles to {output_path}")
        with output_path.open("w", encoding="utf-8") as f:
            f.write(content)

        return output_path

    with create_temp_dir() as temp_dir:
        indices = range(len(streams)) if track is None else [track]
        return [inner_translate(i, to_language, from_language) for i in indices]


def _translate_subtitles_helsinki(content: str, from_language: str, language: str) -> str:
    model_name = f"Helsinki-NLP/opus-mt-{from_language}-{language}"
    logger.info(f"loading translation model '{model_name}'")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

    for line in content.splitlines():
        if line.strip().isdigit() or "-->" in line or not line.strip():
            continue
        inputs = tokenizer.encode(line, return_tensors="pt", truncation=True)
        outputs = model.generate(inputs)
        translated_line = tokenizer.decode(outputs[0], skip_special_tokens=True)
        content = content.replace(line, translated_line)

    return content


def _translate_subtitles_googletrans(content: str, from_language: str, language: str) -> str:
    translator = Translator()
    blocks = parse_srt(content)
    text = INVISIBLE_SEPARATOR.join([line for b in blocks for line in b["lines"]])
    translated = asyncio.run(translator.translate(text, src=from_language, dest=language))
    return rebuild_srt(blocks, translated.text.split(INVISIBLE_SEPARATOR))
