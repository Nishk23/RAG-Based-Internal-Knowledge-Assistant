from __future__ import annotations

import re
from typing import Any

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "was",
    "were",
    "what",
    "when",
    "where",
    "which",
    "who",
    "with",
}


def _tokens(text: str) -> set[str]:
    return {token for token in TOKEN_PATTERN.findall(text.lower()) if token not in STOP_WORDS}


def _coverage(expected: set[str], observed: set[str]) -> float | None:
    if not expected:
        return None
    return len(expected & observed) / len(expected)


def run_quality_evaluation(
    *,
    question: str,
    answer: str,
    contexts: list[str],
    ground_truth: str | None = None,
) -> dict[str, Any]:
    """Return deterministic, zero-data-egress quality indicators.

    These metrics are intentionally reproducible and are not presented as
    substitutes for human review or model-graded evaluation.
    """

    question_tokens = _tokens(question)
    answer_tokens = _tokens(re.sub(r"\[\d+]", "", answer))
    context_token_sets = [_tokens(context) for context in contexts]
    all_context_tokens = set().union(*context_token_sets) if context_token_sets else set()

    context_relevance = [
        _coverage(question_tokens, context_tokens) or 0.0 for context_tokens in context_token_sets
    ]
    relevant_contexts = sum(score > 0 for score in context_relevance)
    citations = {int(value) for value in re.findall(r"\[(\d+)]", answer)}
    valid_citations = {citation for citation in citations if 1 <= citation <= len(contexts)}

    metrics: dict[str, float | None] = {
        "faithfulness": _coverage(answer_tokens, all_context_tokens),
        "answer_relevancy": _coverage(question_tokens, answer_tokens),
        "context_precision": (relevant_contexts / len(contexts) if contexts else None),
        "context_recall": (
            _coverage(_tokens(ground_truth), all_context_tokens) if ground_truth else None
        ),
        "context_relevancy": (
            sum(context_relevance) / len(context_relevance) if context_relevance else None
        ),
        "citation_validity": (len(valid_citations) / len(citations) if citations else 0.0),
    }

    return {
        "status": "success",
        "metrics": metrics,
        "skipped_metrics": ["context_recall"] if ground_truth is None else [],
        "message": "Deterministic quality evaluation completed.",
    }
