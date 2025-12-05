import asyncio
import logging
from pathlib import Path
from typing import Literal

from googletrans import Translator
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from vscripts.constants import INVISIBLE_SEPARATOR, ISO639_3_TO_1, UNKNOWN_LANGUAGE
from vscripts.data.language import find_subs_language
from vscripts.utils import get_output_file_path, parse_srt, rebuild_srt
from vscripts.utils._utils import is_subs

logger = logging.getLogger("vscripts")


def translate_subtitles(
    input_path: Path,
    language: str,
    from_language: str | None = None,
    *,
    output: Path | None = None,
    mode: Literal["local", "google"] = "local",
    **_,
) -> Path:
    """
    Translate subtitle file to specified language using Helsinki-NLP translation models.
    Args:
        input_path (Path): The path to the input subtitle file.
        language (str): The target language code for translation.
        from_language (str | None): The source language code of the input subtitles.
        output (Path | None): The path to save the output translated subtitle file.
        mode (Literal["local", "google"]): Mode to use ("local" for Helsinki-NLP, "google" for Google Translate).
    Returns: The path to the newly created translated subtitle file.
    """
    if not input_path.is_file():
        raise ValueError(f"invalid {input_path=}")
    if not is_subs(input_path):
        raise ValueError(f"{input_path} is not a subtitle file")

    if from_language is None:
        from_language = find_subs_language(input_path)
        logger.info(f"inferred language='{from_language}' for {input_path.name} from audio stream")

    if from_language == UNKNOWN_LANGUAGE:
        logger.warning(f"could not determine language for {input_path.name}, defaulting to 'eng'")
        from_language = "eng"

    if len(from_language) == 3:
        logger.info(f"converting ISO 639-3 from_language code '{from_language}' to ISO 639-1")
        from_language = ISO639_3_TO_1.get(from_language, from_language)
    if len(language) == 3:
        logger.info(f"converting ISO 639-3 language code '{language}' to ISO 639-1")
        language = ISO639_3_TO_1.get(language, language)

    output = get_output_file_path(
        output or input_path.parent,
        default_name=f"{input_path.stem}_{language}.srt",
    )

    with input_path.open("r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    logger.info(f"translating subtitles from '{from_language}' to '{language}'")
    logger.info(f"translation mode: {mode}")
    if mode == "google":
        content = _translate_subtitles_googletrans(content, from_language, language)
    else:
        content = _translate_subtitles_helsinki(content, from_language, language)

    logger.info(f"writing translated subtitles to {output}")
    with output.open("w", encoding="utf-8") as f:
        f.write(content)

    return output


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
