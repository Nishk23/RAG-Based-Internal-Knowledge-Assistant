from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from rank_bm25 import BM25Okapi


@dataclass
class RetrievedChunk:
    chunk_id: str
    document_id: str
    document_name: str
    text: str
    chunk_index: int
    metadata: dict[str, Any]
    created_at: str
    score: float


class BM25VectorlessRetriever:
    """Lexical retriever implementing vectorless RAG.

    This retriever does not create or query embeddings and does not use any vector DB.
    It scores overlap between tokenized query/document chunks using BM25.
    """

    def __init__(self, chunks: list[dict[str, Any]]) -> None:
        self.chunks = chunks
        self.tokenized_corpus = [self._tokenize(c.get("text", "")) for c in chunks]
        self.bm25 = BM25Okapi(self.tokenized_corpus) if self.tokenized_corpus else None

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return re.findall(r"[a-z0-9]+", text.lower())

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[RetrievedChunk]:
        if not self.chunks or self.bm25 is None:
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        scores = self.bm25.get_scores(query_tokens)
        scored_indices = list(enumerate(scores))

        if metadata_filter:
            def match_meta(chunk: dict[str, Any]) -> bool:
                chunk_meta = chunk.get("metadata", {}) or {}
                return all(chunk_meta.get(k) == v for k, v in metadata_filter.items())

            scored_indices = [
                (idx, score)
                for idx, score in scored_indices
                if match_meta(self.chunks[idx])
            ]

        ranked = sorted(scored_indices, key=lambda item: item[1], reverse=True)[:top_k]

        results: list[RetrievedChunk] = []
        for idx, score in ranked:
            chunk = self.chunks[idx]
            results.append(
                RetrievedChunk(
                    chunk_id=str(chunk.get("chunk_id", "")),
                    document_id=str(chunk.get("document_id", "")),
                    document_name=str(chunk.get("document_name", "")),
                    text=str(chunk.get("text", "")),
                    chunk_index=int(chunk.get("chunk_index", 0)),
                    metadata=chunk.get("metadata", {}) or {},
                    created_at=str(chunk.get("created_at", "")),
                    score=float(score),
                )
            )

        return results
