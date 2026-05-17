from __future__ import annotations

import re
from typing import Any


def chunk_text(text: str, chunk_size_words: int, chunk_overlap_words: int) -> list[str]:
    if chunk_size_words <= 0:
        raise ValueError("chunk_size_words must be > 0")
    if chunk_overlap_words < 0:
        raise ValueError("chunk_overlap_words must be >= 0")
    if chunk_overlap_words >= chunk_size_words:
        raise ValueError("chunk_overlap_words must be smaller than chunk_size_words")

    tokens = re.findall(r"\S+", text)
    if not tokens:
        return []

    chunks: list[str] = []
    step = chunk_size_words - chunk_overlap_words
    for start in range(0, len(tokens), step):
        window = tokens[start : start + chunk_size_words]
        if not window:
            continue
        chunks.append(" ".join(window))
        if start + chunk_size_words >= len(tokens):
            break

    return chunks


def build_chunk_records(
    *,
    document_id: str,
    document_name: str,
    chunks: list[str],
    created_at: str,
    base_metadata: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    metadata = base_metadata or {}
    records: list[dict[str, Any]] = []
    for idx, chunk in enumerate(chunks):
        records.append(
            {
                "chunk_id": f"{document_id}_chunk_{idx}",
                "document_id": document_id,
                "document_name": document_name,
                "text": chunk,
                "chunk_index": idx,
                "metadata": metadata,
                "created_at": created_at,
            }
        )
    return records
