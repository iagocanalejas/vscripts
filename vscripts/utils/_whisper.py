import logging
from typing import Literal

from whisper import Whisper, load_model

logger = logging.getLogger("vscripts")

WhisperModel = Literal["small", "medium", "large", "turbo"]

_loaded_whisper_models: dict[WhisperModel, Whisper] = {}


def load_whisper(model: WhisperModel) -> Whisper:
    logger.debug(f"loading whisper model: {model}")
    if model not in _loaded_whisper_models:
        _loaded_whisper_models[model] = load_model(model)
    return _loaded_whisper_models[model]
