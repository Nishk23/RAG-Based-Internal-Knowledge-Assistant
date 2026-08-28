import pytest
from pydantic import ValidationError

from app.evaluation.quality_runner import run_quality_evaluation
from app.schemas import EvaluationRequest


def test_quality_evaluation_scores_grounded_cited_answer() -> None:
    result = run_quality_evaluation(
        question="When are incident updates required?",
        answer="Incident updates are required every 30 minutes [1].",
        contexts=["Incident updates are required every 30 minutes."],
        ground_truth="Updates are required every 30 minutes.",
    )

    assert result["status"] == "success"
    assert result["metrics"]["citation_validity"] == 1.0
    assert result["metrics"]["faithfulness"] == 1.0
    assert result["skipped_metrics"] == []


def test_quality_evaluation_marks_invalid_citation() -> None:
    result = run_quality_evaluation(
        question="What is the policy?",
        answer="The policy is documented [4].",
        contexts=["The policy is documented."],
    )
    assert result["metrics"]["citation_validity"] == 0.0
    assert result["skipped_metrics"] == ["context_recall"]


def test_evaluation_request_bounds_each_context() -> None:
    with pytest.raises(ValidationError):
        EvaluationRequest(question="What is the policy?", answer="Unknown.", contexts=["x" * 20001])
