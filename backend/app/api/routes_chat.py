from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.rag.graph import run_rag_workflow
from app.schemas import ChatRequest, ChatResponse, SourceChunk
from app.storage.document_store import DocumentStore
from app.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["chat"])
store = DocumentStore(settings.store_dir)


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    chunks = store.get_chunks()
    if not chunks:
        raise HTTPException(
            status_code=400,
            detail="No documents available. Upload at least one document before querying.",
        )

    state = run_rag_workflow(
        question=payload.question,
        all_chunks=chunks,
        top_k=payload.top_k,
        evaluate=payload.evaluate,
    )

    errors = state.get("errors", [])
    if errors:
        logger.warning("chat_validation_error", extra={"errors": errors})
        raise HTTPException(status_code=400, detail="; ".join(errors))

    sources = [SourceChunk(**source) for source in state.get("sources", [])]

    return ChatResponse(
        answer=state.get("answer", ""),
        sources=sources,
        retrieval_method="BM25 Vectorless RAG",
        evaluation=state.get("evaluation"),
    )
