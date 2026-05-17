from __future__ import annotations

import importlib
from typing import Any

from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


def _import_metric(name: str) -> Any | None:
    try:
        metrics_module = importlib.import_module("ragas.metrics")
        return getattr(metrics_module, name)
    except Exception as exc:  # noqa: BLE001
        logger.warning("ragas_metric_unavailable", extra={"metric": name, "error": str(exc)})
        return None


def run_ragas_evaluation(
    *,
    question: str,
    answer: str,
    contexts: list[str],
    ground_truth: str | None = None,
) -> dict[str, Any]:
    if not settings.openai_api_key:
        raise RuntimeError(
            "RAGAS evaluation requires OPENAI_API_KEY because LLM-based metrics are used."
        )

    try:
        from datasets import Dataset
        from ragas import evaluate
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Failed to import RAGAS dependencies: {exc}") from exc

    sample = {
        "question": [question],
        "answer": [answer],
        "contexts": [contexts],
    }
    if ground_truth:
        sample["ground_truth"] = [ground_truth]

    dataset = Dataset.from_dict(sample)

    desired_metrics = [
        "faithfulness",
        "answer_relevancy",
        "context_precision",
        "context_recall",
        "context_relevancy",
    ]

    metrics = []
    skipped: list[str] = []
    for metric_name in desired_metrics:
        metric = _import_metric(metric_name)
        if metric is None:
            skipped.append(metric_name)
            continue
        metrics.append(metric)

    if not metrics:
        raise RuntimeError("No compatible RAGAS metrics were available in the installed version.")

    result = evaluate(dataset=dataset, metrics=metrics)
    as_dict = result.to_pandas().iloc[0].to_dict()

    normalized: dict[str, float | None] = {}
    for key, value in as_dict.items():
        if isinstance(value, (int, float)):
            normalized[key] = float(value)
        else:
            normalized[key] = None

    return {
        "status": "success",
        "metrics": normalized,
        "skipped_metrics": skipped,
        "message": "Evaluation completed.",
    }
