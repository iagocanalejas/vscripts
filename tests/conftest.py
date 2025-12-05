from unittest.mock import patch

import pytest
import torch
import whisper


@pytest.fixture(autouse=True)
def before_each():
    if torch.cuda.is_available():  # pragma: no cover
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()


_test_whisper_model = whisper.load_model("tiny")


@pytest.fixture(autouse=True)
def mock_load_whisper():
    """Automatically mock load_whisper in all tests."""
    with patch("vscripts.utils._whisper.load_model", return_value=_test_whisper_model):
        yield
