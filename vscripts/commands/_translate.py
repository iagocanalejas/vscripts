import asyncio
import logging
from pathlib import Path
from typing import Literal

from googletrans import Translator
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from vscripts.constants import INVISIBLE_SEPARATOR, ISO639_1_TO_3, ISO639_3_TO_1, UNKNOWN_LANGUAGE
from vscripts.data.language import find_subs_language
from vscripts.data.streams import FileStreams, SubtitleStream
from vscripts.utils import get_output_file_path, parse_srt, rebuild_srt

logger = logging.getLogger("vscripts")


def translate_subtitles(
    streams: FileStreams,
    to_language: str,
    from_language: str | None = None,
    *,
    track: int | None = None,
    mode: Literal["local", "google"] = "local",
    output: Path | None = None,
    **_,
) -> FileStreams:
    """
    Translate subtitle streams in a multimedia file to a specified target language.
    Args:
        streams (FileStreams): The FileStreams object representing the subtitle file to be translated.
        to_language (str): The target language code for translation.
        from_language (str | None): The source language code of the input subtitles.
        track (int): The index of the subtitle track to use for language inference.
        mode (Literal["local", "google"]): "local" for Helsinki-NLP, "google" for Google Translate.
        output (Path | None): The path to save the output translated subtitle file.
    Returns: The FileStreams object with updated subtitle stream.
    """
    if len(streams.subtitles) < 1:
        raise ValueError(f"no subtitle streams found in {streams.file_path=}, cannot translate")
    if track is not None and (track < 0 or track >= len(streams.subtitles)):
        raise ValueError(f"invalid subtitle track index {track=} for {streams.subtitles=}")
    if track is not None and not streams.subtitles[track].file_path.is_file():
        raise ValueError(f"invalid {streams.subtitles[track].file_path=}")
    if track is None and any(not a.file_path.is_file() for a in streams.subtitles):
        raise ValueError(f"one or more subtitle stream file paths are invalid in {streams.subtitles=}")
    if len(to_language) != 3:
        raise ValueError(f"invalid target language code '{to_language}', must be ISO 639-3")
    if from_language is not None and len(from_language) != 3:
        raise ValueError(f"invalid source language code '{from_language}', must be ISO 639-3")

    def inner_translate(index: int, to_lang: str, lang: str | None) -> None:
        stream = streams.subtitles[index]
        output_path = get_output_file_path(
            output or stream.file_path.parent,
            default_name=f"{stream.file_path.stem}_{to_lang}.srt",
        )

        if lang is None:
            lang = find_subs_language(stream)
            logger.info(f"inferred {lang=} for {stream.index} in {stream.file_path.name}")

        if lang == UNKNOWN_LANGUAGE:  # pragma: no cover
            logger.warning(f"could not determine language for {stream.index}, defaulting to 'eng'")
            lang = "eng"

        if len(lang) == 3:
            logger.debug(f"converting ISO 639-3 from_lang code '{lang}' to ISO 639-1")
            lang = ISO639_3_TO_1.get(lang, lang)
        if len(to_lang) == 3:
            logger.debug(f"converting ISO 639-3 lang code '{to_lang}' to ISO 639-1")
            to_lang = ISO639_3_TO_1.get(to_lang, to_lang)

        with stream.file_path.open("r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        logger.info(f"translating subtitles from '{lang=}' to '{to_lang=}'. {mode=}")
        if mode == "google":
            content = _translate_subtitles_googletrans(content, lang, to_lang)
        else:
            content = _translate_subtitles_helsinki(content, lang, to_lang)

        logger.info(f"writing translated subtitles to {output_path}")
        with output_path.open("w", encoding="utf-8") as f:
            f.write(content)

        new_stream = SubtitleStream(
            _index=0,
            ffmpeg_index=0,
            codec_name="mov_text",
            codec_type="subtitle",
            language=ISO639_1_TO_3.get(to_lang, to_lang),
            generated=True,
        )
        new_stream.file_path = output_path
        streams.subtitles.append(new_stream)

    indices = range(len(streams.subtitles)) if track is None else [track]
    for i in indices:
        inner_translate(i, to_lang=to_language, lang=from_language)

    return streams


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
