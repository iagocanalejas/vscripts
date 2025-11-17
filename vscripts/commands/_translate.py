import logging
from pathlib import Path

from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from vscripts.constants import UNKNOWN_LANGUAGE
from vscripts.data.language import ISO639_3_TO_1, find_language
from vscripts.data.models import ProcessingData
from vscripts.data.streams import CODEC_TYPE_SUBTITLE, SubtitleStream
from vscripts.utils import get_output_file_path, get_streams

logger = logging.getLogger("vscripts")


def translate_subtitles(
    input_path: Path,
    language: str,
    output: Path | None = None,
    from_language: str | None = None,
    extra: ProcessingData | None = None,
) -> Path:
    """
    Translate subtitle file to specified language using Helsinki-NLP translation models.
    Args:
        input_path (Path): The path to the input subtitle file.
        language (str): The target language code for translation.
        output (Path | None): The path to save the output translated subtitle file.
        from_language (str | None): The source language code of the input subtitles.
        extra (ProcessingData | None): Additional processing data.
    Returns: The path to the newly created translated subtitle file.
    """
    if not input_path.is_file():
        raise ValueError(f"invalid {input_path=}")
    streams = get_streams(input_path)
    if len(streams) != 1 or streams[0].get("codec_type") != CODEC_TYPE_SUBTITLE:
        raise ValueError(f"{input_path} must contain exactly one audio stream")

    if from_language is None:
        stream = SubtitleStream.from_file(input_path)[0]
        from_language = find_language(stream)
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

    model_name = f"Helsinki-NLP/opus-mt-{from_language}-{language}"
    logger.info(f"loading translation model '{model_name}'")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

    with input_path.open("r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    for line in content.splitlines():
        if line.strip().isdigit() or "-->" in line or not line.strip():
            continue
        inputs = tokenizer.encode(line, return_tensors="pt", truncation=True)
        outputs = model.generate(inputs)
        translated_line = tokenizer.decode(outputs[0], skip_special_tokens=True)
        content = content.replace(line, translated_line)

    logger.info(f"writing translated subtitles to {output}")
    with output.open("w", encoding="utf-8") as f:
        f.write(content)

    return output
