from types import SimpleNamespace

import pytest
from pydantic import SecretStr

from app.config import settings
from app.rag.rag_chain import (
    INSUFFICIENT_CONTEXT,
    CitationValidationError,
    ModelConfigurationError,
    build_context_text,
    generate_answer,
)

CHUNKS = [{"document_name": "policy.md", "score": 1.0, "text": "Policy evidence."}]


def test_context_is_numbered_and_empty_context_abstains() -> None:
    assert build_context_text(CHUNKS).startswith("[1] policy.md")
    assert generate_answer("question", []) == INSUFFICIENT_CONTEXT


def test_generation_requires_provider_configuration(monkeypatch) -> None:
    monkeypatch.setattr(settings, "openai_api_key", None)
    with pytest.raises(ModelConfigurationError):
        generate_answer("question", CHUNKS)


def test_generation_rejects_invalid_citations(monkeypatch) -> None:
    class FakeModel:
        def __init__(self, **_kwargs) -> None:
            pass

        def invoke(self, _messages):
            return SimpleNamespace(content="Unsupported response without a citation.")

    monkeypatch.setattr(settings, "openai_api_key", SecretStr("test-key"))
    monkeypatch.setattr("app.rag.rag_chain.ChatOpenAI", FakeModel)
    with pytest.raises(CitationValidationError):
        generate_answer("question", CHUNKS)


def test_generation_accepts_valid_citation(monkeypatch) -> None:
    class FakeModel:
        def __init__(self, **_kwargs) -> None:
            pass

        def invoke(self, _messages):
            return SimpleNamespace(content="Policy evidence [1].")

    monkeypatch.setattr(settings, "openai_api_key", SecretStr("test-key"))
    monkeypatch.setattr("app.rag.rag_chain.ChatOpenAI", FakeModel)
    assert generate_answer("question", CHUNKS) == "Policy evidence [1]."
