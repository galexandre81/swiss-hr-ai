from __future__ import annotations

import threading
from unittest.mock import MagicMock, patch

import pytest
import requests

from _app.core.llm_client import (
    GenerationCancelled,
    LLMClient,
    LLMStatus,
)


def test_refuses_non_local_url(sandbox):
    with pytest.raises(RuntimeError):
        LLMClient(base_url="http://evil.example.com/v1")


def test_status_unreachable_when_connection_refused(sandbox):
    client = LLMClient()
    with patch("_app.core.llm_client.requests.get",
               side_effect=requests.exceptions.ConnectionError()):
        info = client.status()
    assert info.status is LLMStatus.UNREACHABLE


def test_status_no_model_when_empty_list(sandbox):
    client = LLMClient()
    mock_resp = MagicMock(status_code=200)
    mock_resp.json.return_value = {"data": []}
    with patch("_app.core.llm_client.requests.get", return_value=mock_resp):
        info = client.status()
    assert info.status is LLMStatus.NO_MODEL


def test_status_ready_auto_detects_first_model(sandbox):
    client = LLMClient()  # modèle non-configuré
    mock_resp = MagicMock(status_code=200)
    mock_resp.json.return_value = {"data": [
        {"id": "qwen3-8b-instruct"}, {"id": "mistral-7b"}
    ]}
    with patch("_app.core.llm_client.requests.get", return_value=mock_resp):
        info = client.status()
    assert info.status is LLMStatus.READY
    assert info.active_model == "qwen3-8b-instruct"
    assert client.model == "qwen3-8b-instruct"


def test_status_prefers_configured_model_when_available(sandbox):
    client = LLMClient(model="mistral-7b")
    mock_resp = MagicMock(status_code=200)
    mock_resp.json.return_value = {"data": [
        {"id": "qwen3-8b-instruct"}, {"id": "mistral-7b"}
    ]}
    with patch("_app.core.llm_client.requests.get", return_value=mock_resp):
        info = client.status()
    assert info.active_model == "mistral-7b"


def test_stream_cancellation_raises(sandbox):
    client = LLMClient(model="test-model")
    cancel = threading.Event()
    cancel.set()

    # Mock d'une réponse SSE-like
    mock_post = MagicMock()
    mock_post.__enter__.return_value.iter_lines.return_value = iter([
        "data: " + '{"choices":[{"delta":{"content":"Hel"}}]}',
        "data: " + '{"choices":[{"delta":{"content":"lo"}}]}',
    ])
    mock_post.__enter__.return_value.raise_for_status = lambda: None
    mock_post.__exit__ = MagicMock(return_value=False)

    with patch("_app.core.llm_client.requests.post", return_value=mock_post):
        gen = client.generate("x", temperature=0.1, stream=True, cancel_event=cancel)
        with pytest.raises(GenerationCancelled):
            list(gen)
