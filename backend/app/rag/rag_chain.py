from __future__ import annotations

from typing import Any

from langchain_openai import ChatOpenAI

from app.config import settings
from app.rag.prompts import ANSWER_PROMPT


def build_context_text(retrieved_chunks: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for idx, chunk in enumerate(retrieved_chunks, start=1):
        lines.append(
            f"[{idx}] {chunk.get('document_name', 'Unknown')} | score={chunk.get('score', 0.0):.4f}\n"
            f"{chunk.get('text', '')}"
        )
    return "\n\n".join(lines)


def generate_answer(question: str, retrieved_chunks: list[dict[str, Any]]) -> str:
    if not retrieved_chunks:
        return "I could not find relevant context in the uploaded documents."

    if not settings.openai_api_key:
        return (
            "Backend is running and retrieval worked, but answer generation requires "
            "OPENAI_API_KEY in environment variables."
        )

    context = build_context_text(retrieved_chunks)
    prompt_value = ANSWER_PROMPT.invoke({"question": question, "context": context})

    llm = ChatOpenAI(model=settings.openai_model, api_key=settings.openai_api_key)
    response = llm.invoke(prompt_value.messages)
    return str(response.content).strip()
