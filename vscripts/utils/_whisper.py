from typing import Literal

import whisper

WhisperModel = Literal["small", "medium", "large", "turbo"]

_loaded_whisper_models: dict[WhisperModel, whisper.Whisper] = {}


def load_whisper(model: WhisperModel) -> whisper.Whisper:
    if model not in _loaded_whisper_models:
        _loaded_whisper_models[model] = whisper.load_model(model)
    return _loaded_whisper_models[model]
