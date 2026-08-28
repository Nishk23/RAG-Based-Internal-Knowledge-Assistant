from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from app.config import settings
from app.dependencies import store
from app.evaluation.quality_runner import run_quality_evaluation
from app.schemas import EvaluationRequest, EvaluationResponse
from app.security.auth import Principal, require_roles
from app.security.rate_limit import rate_limit
from app.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["evaluation"])
evaluation_admin = require_roles("admin")
evaluation_rate_limit = rate_limit("evaluation", settings.rate_limit_evaluation)


@router.post("/evaluate", response_model=EvaluationResponse)
def evaluate(
    payload: EvaluationRequest,
    request: Request,
    principal: Principal = Depends(evaluation_admin),
    _: None = Depends(evaluation_rate_limit),
) -> EvaluationResponse:
    try:
        result = run_quality_evaluation(
            question=payload.question,
            answer=payload.answer,
            contexts=payload.contexts,
            ground_truth=payload.ground_truth,
        )
    except Exception as exc:
        logger.exception("evaluation_unexpected_error")
        raise HTTPException(status_code=500, detail="Unexpected evaluation error.") from exc

    store.record_audit_event(
        tenant_id=principal.tenant_id,
        subject=principal.subject,
        action="quality.evaluate",
        resource_type="evaluation",
        outcome="success",
        request_id=getattr(request.state, "request_id", None),
        metadata={"context_count": len(payload.contexts)},
    )
    return EvaluationResponse(**result)
