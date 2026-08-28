from __future__ import annotations

import re
from typing import Any

from langchain_openai import ChatOpenAI

from app.config import settings
from app.rag.prompts import ANSWER_PROMPT

INSUFFICIENT_CONTEXT = "I could not find sufficient authorized evidence in the knowledge base."


class ModelConfigurationError(RuntimeError):
    pass


class CitationValidationError(RuntimeError):
    pass


def build_context_text(retrieved_chunks: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for idx, chunk in enumerate(retrieved_chunks, start=1):
        source_label = chunk.get("document_name", "Unknown")
        source_score = chunk.get("score", 0.0)
        lines.append(f"[{idx}] {source_label} | score={source_score:.4f}\n{chunk.get('text', '')}")
    return "\n\n".join(lines)


def generate_answer(question: str, retrieved_chunks: list[dict[str, Any]]) -> str:
    if not retrieved_chunks:
        return INSUFFICIENT_CONTEXT

    if not settings.openai_api_key:
        raise ModelConfigurationError(
            "Answer generation is unavailable because the model provider is not configured."
        )

    context = build_context_text(retrieved_chunks)
    prompt_value = ANSWER_PROMPT.invoke({"question": question, "context": context})

    llm = ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key.get_secret_value(),
        base_url=settings.openai_base_url,
        timeout=settings.llm_timeout_seconds,
        max_retries=settings.llm_max_retries,
        temperature=0,
    )
    response = llm.invoke(prompt_value.to_messages())
    answer = str(response.content).strip()
    if answer == INSUFFICIENT_CONTEXT:
        return answer

    citations = {int(value) for value in re.findall(r"\[(\d+)]", answer)}
    if not citations or any(value < 1 or value > len(retrieved_chunks) for value in citations):
        raise CitationValidationError("The model response did not contain valid source citations.")
    return answer
