from __future__ import annotations

from hashlib import sha256

from fastapi import APIRouter, Depends, HTTPException, Request

from app.config import settings
from app.dependencies import store
from app.rag.graph import run_rag_workflow
from app.rag.rag_chain import CitationValidationError, ModelConfigurationError
from app.schemas import ChatRequest, ChatResponse, SourceChunk
from app.security.auth import Principal, require_roles
from app.security.rate_limit import rate_limit
from app.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["chat"])
chat_reader = require_roles("reader", "editor", "admin")
chat_rate_limit = rate_limit("chat", settings.rate_limit_chat)


@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    request: Request,
    principal: Principal = Depends(chat_reader),
    _: None = Depends(chat_rate_limit),
) -> ChatResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    chunks = store.get_chunks(principal.tenant_id, principal.roles)
    if not chunks:
        raise HTTPException(
            status_code=400,
            detail="No authorized documents are available for this request.",
        )

    try:
        state = run_rag_workflow(
            question=payload.question,
            all_chunks=chunks,
            top_k=payload.top_k,
            evaluate=payload.evaluate,
        )
    except ModelConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except CitationValidationError as exc:
        logger.warning("answer_citation_validation_failed")
        raise HTTPException(
            status_code=502,
            detail="The model response failed source-citation validation.",
        ) from exc
    except Exception as exc:
        logger.exception("chat_generation_failed")
        raise HTTPException(status_code=502, detail="The model provider request failed.") from exc

    errors = state.get("errors", [])
    if errors:
        raise HTTPException(status_code=400, detail="; ".join(errors))

    sources = [SourceChunk(**source) for source in state.get("sources", [])]
    question_digest = sha256(payload.question.encode("utf-8")).hexdigest()
    store.record_audit_event(
        tenant_id=principal.tenant_id,
        subject=principal.subject,
        action="knowledge.query",
        resource_type="knowledge_base",
        outcome="success",
        request_id=request_id,
        metadata={
            "question_sha256": question_digest,
            "source_count": len(sources),
            "evaluated": payload.evaluate,
        },
    )
    return ChatResponse(
        answer=state.get("answer", ""),
        sources=sources,
        retrieval_method="ACL-filtered BM25 + character TF-IDF",
        evaluation=state.get("evaluation"),
        request_id=request_id,
    )
