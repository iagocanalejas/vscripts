import logging
import random
from collections import Counter
from pathlib import Path
from typing import Any, Literal

import whisper
from fast_langdetect import detect
from lhotse import MonoCut, Recording

from pyutils.paths import create_temp_dir
from vscripts.constants import UNKNOWN_LANGUAGE
from vscripts.data.streams import AudioStream, SubtitleStream
from vscripts.utils import WhisperModel, load_whisper

logger = logging.getLogger("vscripts")


NUM_SAMPLES = 10
SAMPLE_DURATION = 30.0

ISO639_1_TO_3 = {
    "en": "eng",
    "fr": "fra",
    "de": "deu",
    "es": "spa",
    "gl": "glg",
    "it": "ita",
    "zh": "zho",
    "ja": "jpn",
}
ISO639_3_TO_1 = {v: k for k, v in ISO639_1_TO_3.items()}


def find_language(stream: AudioStream | SubtitleStream, force_detection: bool = False) -> str:
    """
    Detect the language of a given stream (audio or subtitle).
    Args:
        stream (AudioStream | SubtitleStream): The stream to analyze.
        force_detection (bool): Whether to force detection even if metadata exists.
    Returns:
        str: The detected language code in ISO 639-3 format, or "unk" if undetermined.
    """
    if isinstance(stream, AudioStream):
        return find_audio_language(stream, force_detection=force_detection)
    elif isinstance(stream, SubtitleStream):
        return find_subs_language(stream, force_detection=force_detection)


_MODEL_MAP: dict[WhisperModel, Literal["lite", "full", "auto"]] = {
    "small": "lite",
    "medium": "auto",
    "large": "full",
    "turbo": "auto",
}


def find_subs_language(
    stream: SubtitleStream,
    model_name: WhisperModel = "turbo",
    force_detection: bool = False,
) -> str:
    """
    Detect the language of a subtitle stream using its content.
    Args:
        stream (SubtitleStream): The subtitle stream to analyze.
        model_name (FastLangDetectModel): The language detection model to use.
        force_detection (bool): Whether to force detection even if metadata exists.
    Returns:
        str: The detected language code in ISO 639-3 format, or "unk" if undetermined.
    """
    lang = None
    if not stream.file_path.is_file():
        logger.warning(f"subtitle file not found: {stream.file_path}")
        return UNKNOWN_LANGUAGE

    if not force_detection:
        lang = stream.tags.get("language", None)
        if lang and _valid_lang(lang):
            return _convert_lang_code(lang)

    with stream.file_path.open("r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    t = detect(content, model=_MODEL_MAP[model_name], k=3)
    if len(t) > 0:
        if float(t[0]["score"]) < 0.8:
            logger.warning(f"low confidence for detected language: {t[0]['score']:.2f}")
        lang = str(t[0]["lang"])
    return _convert_lang_code(lang) if lang else UNKNOWN_LANGUAGE


def find_audio_language(
    stream: AudioStream,
    model_name: WhisperModel = "turbo",
    num_samples: int = NUM_SAMPLES,
    force_detection: bool = False,
) -> str:
    """
    Detect the language of an audio stream using sampled segments.
    Args:
        stream (AudioStream): The audio stream to analyze.
        model_name (WhisperModel): The Whisper model to use for transcription.
        num_samples (int): The number of audio samples to analyze.
        force_detection (bool): Whether to force detection even if metadata exists.
    Returns:
        str: The detected language code in ISO 639-3 format, or "unk"
    """
    lang = None
    if not force_detection:
        lang = stream.tags.get("language", None)
        if lang and _valid_lang(lang):
            return _convert_lang_code(lang)

    rec = Recording.from_file(str(stream.file_path))
    samples = [(stream.file_path, 0.0, rec.duration)]
    model = load_whisper(model_name)

    if rec.duration < 2 * SAMPLE_DURATION:
        logger.info(f"audio duration {rec.duration:.2f}s is too short for sampling, analyzing full audio")
        return _convert_lang_code(_analyze_language(samples[0], model)["language"])

    with create_temp_dir() as temp_dir:
        logger.info(f"sampling audio in {num_samples} parts for language detection")
        samples = []
        for i in range(num_samples):
            out_path = Path(temp_dir) / f"sample_{i}.wav"
            start = random.uniform(0, max(0, rec.duration - SAMPLE_DURATION))

            MonoCut(
                id=f"sample_{i}",
                start=start,
                duration=SAMPLE_DURATION,
                channel=rec.channel_ids[0] if rec.channel_ids is not None else 0,
                recording=rec,
            ).save_audio(str(out_path))
            logger.debug(f"sampled audio: {out_path} [{start:.2f}s - {start + SAMPLE_DURATION:.2f}s]")
            samples.append((out_path, start, start + SAMPLE_DURATION))
        results = [_analyze_language(s, model) for s in samples]

    lang_counts = Counter[str](res["language"] for res in results)
    if len(lang_counts) == 0:
        logger.warning("no languages detected from audio samples")
        return UNKNOWN_LANGUAGE

    logger.info(f"found languages: {lang_counts}")
    lang = lang_counts.most_common(1)[0][0]
    return _convert_lang_code(lang)


def _convert_lang_code(lang: str) -> str:
    if lang is None or len(lang) == 3:
        return lang
    if len(lang) == 2 and lang in ISO639_1_TO_3:
        return ISO639_1_TO_3.get(lang, UNKNOWN_LANGUAGE)
    logger.warning(f"unknown ISO 639-1 code: {lang}")
    return lang


def _analyze_language(sample: tuple[Path, float, float], model: whisper.Whisper) -> dict[str, Any]:
    path, start, end = sample
    logger.debug(f"analyzing language for sample: {path} [{start:.2f}s - {end:.2f}s]")
    result = model.transcribe(str(path), language=None)
    return {
        "file": path,
        "start": start,
        "end": end,
        "language": result["language"],
        "text": str(result["text"]).strip(),
    }


def _valid_lang(lang: str) -> bool:
    return lang not in ("und", "unk", "")
