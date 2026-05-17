from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class DocumentSummary(BaseModel):
    document_id: str
    document_name: str
    chunk_count: int
    created_at: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class UploadResponse(BaseModel):
    document_id: str
    document_name: str
    chunk_count: int
    message: str


class SampleLoadResponse(BaseModel):
    documents_loaded: int
    chunks_indexed: int
    message: str


class DocumentListResponse(BaseModel):
    documents: list[DocumentSummary]


class ChatRequest(BaseModel):
    question: str = Field(min_length=3)
    top_k: int = Field(default=5, ge=1, le=20)
    evaluate: bool = False


class SourceChunk(BaseModel):
    document_name: str
    chunk_id: str
    text: str
    score: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]
    retrieval_method: str
    evaluation: dict[str, Any] | None = None


class EvaluationRequest(BaseModel):
    question: str
    answer: str
    contexts: list[str]
    ground_truth: str | None = None


class EvaluationResponse(BaseModel):
    status: str
    metrics: dict[str, float | None]
    skipped_metrics: list[str]
    message: str
