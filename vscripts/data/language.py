import logging
from typing import Any, Literal, cast

import whisper
from fast_langdetect import detect

from vscripts.constants import UNKNOWN_LANGUAGE
from vscripts.data.streams import AudioStream, SubtitleStream
from vscripts.utils import WhisperModel, flatten_srt_text, load_whisper

logger = logging.getLogger("vscripts")


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
    model_name: WhisperModel = "medium",
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
    if not force_detection:
        lang = stream.tags.get("language", None)
        if lang and _valid_lang(lang):
            lang = _convert_lang_code(lang)
            logger.info(f"using existing subtitle language metadata: {lang}")
            return lang

    with stream.file_path.open("r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    t = detect(flatten_srt_text(content), model=_MODEL_MAP[model_name], k=3)
    if len(t) > 0:
        lang = str(t[0]["lang"])
        if float(t[0]["score"]) < 0.8:
            logger.warning(f"low confidence for detected subtitle language '{lang}': {t[0]['score']:.2f}")
    lang = _convert_lang_code(lang) if lang else UNKNOWN_LANGUAGE
    logger.info(f"determined subtitle language as: {lang}")
    return lang


def find_audio_language(
    stream: AudioStream,
    model_name: WhisperModel = "medium",
    force_detection: bool = False,
) -> str:
    """
    Detect the language of an audio stream using sampled segments.
    Args:
        stream (AudioStream): The audio stream to analyze.
        model_name (WhisperModel): The Whisper model to use for transcription.
        force_detection (bool): Whether to force detection even if metadata exists.
    Returns:
        str: The detected language code in ISO 639-3 format, or "unk"
    """
    lang = None
    if not force_detection:
        lang = stream.tags.get("language", None)
        if lang and _valid_lang(lang):
            lang = _convert_lang_code(lang)
            logger.info(f"using existing audio language metadata: {lang}")
            return lang

    model = load_whisper(model_name)
    audio = whisper.load_audio(str(stream.file_path))
    audio = whisper.pad_or_trim(audio)

    mel = whisper.log_mel_spectrogram(audio, n_mels=model.dims.n_mels).to(model.device)

    _, probs = cast(tuple[Any, dict[str, float]], model.detect_language(mel))
    logger.debug(f"found audio languages: {probs}")
    lang = _convert_lang_code(max(probs.items(), key=lambda x: x[1])[0])
    logger.info(f"determined audio language as: {lang}")
    return lang


def _convert_lang_code(lang: str) -> str:
    if lang is None or len(lang) == 3:
        return lang
    if len(lang) == 2 and lang in ISO639_1_TO_3:
        return ISO639_1_TO_3.get(lang, UNKNOWN_LANGUAGE)
    logger.warning(f"unknown ISO 639-1 code: {lang}")
    return lang


def _valid_lang(lang: str) -> bool:
    return lang not in ("und", "unk", "")
