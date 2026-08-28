from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status

from app.config import settings
from app.dependencies import store
from app.rag.chunker import build_chunk_records, chunk_text
from app.rag.document_loader import (
    MalwareDetectedError,
    UnsafeUploadError,
    UnsupportedFileTypeError,
    extract_text_from_upload,
)
from app.schemas import (
    DeleteResponse,
    DocumentListResponse,
    DocumentSummary,
    SampleLoadResponse,
    UploadResponse,
)
from app.security.auth import VALID_ROLES, Principal, require_roles
from app.security.rate_limit import rate_limit
from app.storage.document_store import (
    DocumentNotFoundError,
    DuplicateDocumentError,
)
from app.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])
document_reader = require_roles("reader", "editor", "admin")
document_editor = require_roles("editor", "admin")
document_admin = require_roles("admin")
upload_rate_limit = rate_limit("document_upload", settings.rate_limit_upload)


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def _parse_allowed_roles(value: str) -> list[str]:
    roles = sorted({role.strip() for role in value.split(",") if role.strip()})
    if not roles or not set(roles) <= VALID_ROLES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="allowed_roles must contain reader, editor, and/or admin.",
        )
    return roles


def _ingest_text(
    *,
    text: str,
    raw_bytes: bytes,
    document_name: str,
    content_type: str,
    allowed_roles: list[str],
    principal: Principal,
) -> tuple[str, int, str]:
    created_at = datetime.now(UTC)
    document_id = str(uuid4())
    checksum = sha256(raw_bytes).hexdigest()

    chunks = chunk_text(
        text=text,
        chunk_size_words=settings.chunk_size_words,
        chunk_overlap_words=settings.chunk_overlap_words,
    )
    if not chunks:
        raise HTTPException(status_code=400, detail="Unable to generate chunks from document.")

    metadata = {
        "content_type": content_type,
        "chunk_size_words": settings.chunk_size_words,
        "chunk_overlap_words": settings.chunk_overlap_words,
        "checksum_sha256": checksum,
    }
    chunk_records = build_chunk_records(
        document_id=document_id,
        tenant_id=principal.tenant_id,
        document_name=document_name,
        chunks=chunks,
        created_at=created_at,
        allowed_roles=allowed_roles,
        base_metadata=metadata,
    )
    store.add_document_with_chunks(
        {
            "document_id": document_id,
            "tenant_id": principal.tenant_id,
            "document_name": document_name,
            "content_type": content_type,
            "checksum": checksum,
            "chunk_count": len(chunk_records),
            "allowed_roles": allowed_roles,
            "created_by": principal.subject,
            "created_at": created_at,
            "metadata": metadata,
        },
        chunk_records,
    )
    return document_id, len(chunk_records), checksum


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    allowed_roles: str = Form("reader,editor,admin"),
    principal: Principal = Depends(document_editor),
    _: None = Depends(upload_rate_limit),
) -> UploadResponse:
    roles = _parse_allowed_roles(allowed_roles)
    try:
        filename, text, raw_bytes = await extract_text_from_upload(file)
        if not text.strip():
            raise HTTPException(status_code=400, detail="Uploaded document is empty.")
        document_id, chunk_count, checksum = _ingest_text(
            text=text,
            raw_bytes=raw_bytes,
            document_name=filename,
            content_type=file.content_type or "application/octet-stream",
            allowed_roles=roles,
            principal=principal,
        )
    except (UnsupportedFileTypeError, UnsafeUploadError, MalwareDetectedError) as exc:
        store.record_audit_event(
            tenant_id=principal.tenant_id,
            subject=principal.subject,
            action="document.upload",
            resource_type="document",
            outcome="rejected",
            request_id=_request_id(request),
            metadata={"reason": type(exc).__name__},
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except DuplicateDocumentError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    store.record_audit_event(
        tenant_id=principal.tenant_id,
        subject=principal.subject,
        action="document.upload",
        resource_type="document",
        resource_id=document_id,
        outcome="success",
        request_id=_request_id(request),
        metadata={"chunk_count": chunk_count, "allowed_roles": roles},
    )
    logger.info(
        "document_uploaded",
        extra={"document_id": document_id, "chunk_count": chunk_count},
    )
    return UploadResponse(
        document_id=document_id,
        document_name=filename,
        chunk_count=chunk_count,
        checksum=checksum,
        message="Document uploaded and transactionally indexed.",
    )


@router.post("/load-sample", response_model=SampleLoadResponse)
def load_sample_documents(
    request: Request,
    principal: Principal = Depends(document_editor),
    _: None = Depends(upload_rate_limit),
) -> SampleLoadResponse:
    sample_dir = Path(__file__).resolve().parents[2] / "sample_docs"
    sample_files = sorted(sample_dir.glob("*.md"))
    if not sample_files:
        raise HTTPException(status_code=404, detail="No sample documents are available.")

    loaded_docs = 0
    total_chunks = 0
    for file_path in sample_files:
        raw_bytes = file_path.read_bytes()
        try:
            _document_id, chunk_count, _checksum = _ingest_text(
                text=raw_bytes.decode("utf-8"),
                raw_bytes=raw_bytes,
                document_name=file_path.name,
                content_type="text/markdown",
                allowed_roles=["reader", "editor", "admin"],
                principal=principal,
            )
        except DuplicateDocumentError:
            continue
        loaded_docs += 1
        total_chunks += chunk_count

    store.record_audit_event(
        tenant_id=principal.tenant_id,
        subject=principal.subject,
        action="document.load_sample",
        resource_type="document_collection",
        outcome="success",
        request_id=_request_id(request),
        metadata={"documents_loaded": loaded_docs, "chunks_indexed": total_chunks},
    )
    return SampleLoadResponse(
        documents_loaded=loaded_docs,
        chunks_indexed=total_chunks,
        message="Sample documents loaded; existing checksums were skipped.",
    )


@router.get("", response_model=DocumentListResponse)
def list_documents(
    principal: Principal = Depends(document_reader),
) -> DocumentListResponse:
    documents = [
        DocumentSummary(**document)
        for document in store.get_documents(principal.tenant_id, principal.roles)
    ]
    return DocumentListResponse(documents=documents)


@router.delete("/{document_id}", response_model=DeleteResponse)
def delete_document(
    document_id: str,
    request: Request,
    principal: Principal = Depends(document_admin),
) -> DeleteResponse:
    try:
        store.delete_document(principal.tenant_id, document_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    store.record_audit_event(
        tenant_id=principal.tenant_id,
        subject=principal.subject,
        action="document.delete",
        resource_type="document",
        resource_id=document_id,
        outcome="success",
        request_id=_request_id(request),
    )
    return DeleteResponse(document_id=document_id, message="Document deleted.")
