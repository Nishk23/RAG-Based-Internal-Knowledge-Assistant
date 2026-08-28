from __future__ import annotations

from typing import Annotated, Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class ReadinessResponse(BaseModel):
    status: str
    checks: dict[str, str]


class DocumentSummary(BaseModel):
    document_id: str
    document_name: str
    chunk_count: int
    created_at: str
    allowed_roles: list[str]
    metadata: dict[str, Any] = Field(default_factory=dict)


class UploadResponse(BaseModel):
    document_id: str
    document_name: str
    chunk_count: int
    checksum: str
    message: str


class SampleLoadResponse(BaseModel):
    documents_loaded: int
    chunks_indexed: int
    message: str


class DocumentListResponse(BaseModel):
    documents: list[DocumentSummary]


class ChatRequest(BaseModel):
    question: str = Field(min_length=3, max_length=4000)
    top_k: int = Field(default=5, ge=1, le=20)
    evaluate: bool = False


class SourceChunk(BaseModel):
    citation_index: int
    document_name: str
    chunk_id: str
    text: str
    score: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]
    retrieval_method: str
    evaluation: dict[str, Any] | None = None
    request_id: str


class EvaluationRequest(BaseModel):
    question: str = Field(min_length=3, max_length=4000)
    answer: str = Field(min_length=1, max_length=20000)
    contexts: list[Annotated[str, Field(min_length=1, max_length=20000)]] = Field(
        min_length=1, max_length=20
    )
    ground_truth: str | None = Field(default=None, max_length=20000)


class EvaluationResponse(BaseModel):
    status: str
    metrics: dict[str, float | None]
    skipped_metrics: list[str]
    message: str


class DeleteResponse(BaseModel):
    document_id: str
    message: str


class PrincipalResponse(BaseModel):
    subject: str
    tenant_id: str
    roles: list[str]


class AuditEvent(BaseModel):
    event_id: str
    subject: str
    action: str
    resource_type: str
    resource_id: str | None
    outcome: str
    request_id: str | None
    metadata: dict[str, Any]
    created_at: str


class AuditEventListResponse(BaseModel):
    events: list[AuditEvent]
