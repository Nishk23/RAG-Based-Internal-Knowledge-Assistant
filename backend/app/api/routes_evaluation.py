from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.evaluation.ragas_runner import run_ragas_evaluation
from app.schemas import EvaluationRequest, EvaluationResponse
from app.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["evaluation"])


@router.post("/evaluate", response_model=EvaluationResponse)
def evaluate(payload: EvaluationRequest) -> EvaluationResponse:
    try:
        result = run_ragas_evaluation(
            question=payload.question,
            answer=payload.answer,
            contexts=payload.contexts,
            ground_truth=payload.ground_truth,
        )
        return EvaluationResponse(**result)
    except RuntimeError as exc:
        logger.warning("evaluation_runtime_error", extra={"error": str(exc)})
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("evaluation_unexpected_error")
        raise HTTPException(status_code=500, detail="Unexpected evaluation error.") from exc
