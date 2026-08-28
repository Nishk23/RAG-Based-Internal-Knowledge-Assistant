from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.config import settings


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
    """Confidence-gated hybrid sparse retriever.

    BM25 token ranking is fused with character n-gram TF-IDF similarity. Access
    filtering happens before either index is built, so unauthorized chunks never
    participate in ranking or inverse-document-frequency calculations.
    """

    def __init__(self, chunks: list[dict[str, Any]]) -> None:
        self.chunks = chunks

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return re.findall(r"[a-z0-9]+", text.lower())

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[RetrievedChunk]:
        if not self.chunks:
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        candidate_indices = list(range(len(self.chunks)))
        if metadata_filter:

            def match_meta(chunk: dict[str, Any]) -> bool:
                chunk_meta = chunk.get("metadata", {}) or {}
                return all(chunk_meta.get(k) == v for k, v in metadata_filter.items())

            candidate_indices = [idx for idx in candidate_indices if match_meta(self.chunks[idx])]
        if not candidate_indices:
            return []

        candidate_texts = [str(self.chunks[idx].get("text", "")) for idx in candidate_indices]
        tokenized_corpus = [self._tokenize(text) for text in candidate_texts]
        bm25 = BM25Okapi(tokenized_corpus)
        bm25_scores = [max(float(score), 0.0) for score in bm25.get_scores(query_tokens)]
        bm25_max = max(bm25_scores, default=0.0)
        normalized_bm25 = [score / bm25_max if bm25_max > 0 else 0.0 for score in bm25_scores]

        try:
            vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=1)
            matrix = vectorizer.fit_transform([*candidate_texts, query])
            tfidf_scores = cosine_similarity(matrix[-1], matrix[:-1]).flatten().tolist()
        except ValueError:
            tfidf_scores = [0.0] * len(candidate_indices)

        scored_indices = [
            (candidate_idx, (0.65 * bm25_score) + (0.35 * tfidf_score))
            for candidate_idx, bm25_score, tfidf_score in zip(
                candidate_indices, normalized_bm25, tfidf_scores, strict=True
            )
        ]
        max_score = max((score for _, score in scored_indices), default=0.0)
        if max_score < settings.retrieval_min_score:
            return []
        relative_floor = max_score * settings.retrieval_min_relative_score
        ranked = [
            item
            for item in sorted(scored_indices, key=lambda item: item[1], reverse=True)
            if item[1] >= settings.retrieval_min_score and item[1] >= relative_floor
        ][:top_k]

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
