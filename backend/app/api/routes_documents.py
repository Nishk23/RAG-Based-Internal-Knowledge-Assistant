from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.config import settings
from app.rag.chunker import build_chunk_records, chunk_text
from app.rag.document_loader import UnsupportedFileTypeError, extract_text_from_upload
from app.schemas import DocumentListResponse, DocumentSummary, SampleLoadResponse, UploadResponse
from app.storage.document_store import DocumentStore
from app.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])
store = DocumentStore(settings.store_dir)


def _ingest_text(
    *,
    text: str,
    document_name: str,
    content_type: str,
) -> tuple[str, int]:
    created_at = datetime.now(timezone.utc).isoformat()
    document_id = str(uuid4())

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
    }

    chunk_records = build_chunk_records(
        document_id=document_id,
        document_name=document_name,
        chunks=chunks,
        created_at=created_at,
        base_metadata=metadata,
    )

    store.add_document(
        {
            "document_id": document_id,
            "document_name": document_name,
            "chunk_count": len(chunk_records),
            "created_at": created_at,
            "metadata": metadata,
        }
    )
    store.add_chunks(chunk_records)
    return document_id, len(chunk_records)


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)) -> UploadResponse:
    filename = file.filename or "uploaded_file"

    try:
        text = extract_text_from_upload(file)
    except UnsupportedFileTypeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not text.strip():
        raise HTTPException(status_code=400, detail="Uploaded document is empty.")

    document_id, chunk_count = _ingest_text(
        text=text,
        document_name=filename,
        content_type=file.content_type or "application/octet-stream",
    )

    logger.info(
        "document_uploaded",
        extra={
            "document_id": document_id,
            "document_name": filename,
            "chunk_count": chunk_count,
        },
    )

    return UploadResponse(
        document_id=document_id,
        document_name=filename,
        chunk_count=chunk_count,
        message="Document uploaded and indexed with BM25 vectorless retrieval.",
    )


@router.post("/load-sample", response_model=SampleLoadResponse)
def load_sample_documents() -> SampleLoadResponse:
    sample_dir = settings.store_dir.parent / "sample_docs"
    sample_files = sorted(sample_dir.glob("*.md"))
    if not sample_files:
        raise HTTPException(status_code=404, detail="No sample docs found in backend/sample_docs.")

    loaded_docs = 0
    total_chunks = 0

    for file_path in sample_files:
        try:
            content = Path(file_path).read_text(encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "sample_doc_read_failed",
                extra={"file": str(file_path), "error": str(exc)},
            )
            continue

        if not content.strip():
            continue

        _, chunk_count = _ingest_text(
            text=content,
            document_name=file_path.name,
            content_type="text/markdown",
        )
        loaded_docs += 1
        total_chunks += chunk_count

    logger.info(
        "sample_docs_loaded",
        extra={"documents_loaded": loaded_docs, "chunks_indexed": total_chunks},
    )
    return SampleLoadResponse(
        documents_loaded=loaded_docs,
        chunks_indexed=total_chunks,
        message="Sample documents loaded into local store.",
    )


@router.get("", response_model=DocumentListResponse)
def list_documents() -> DocumentListResponse:
    docs = [DocumentSummary(**doc) for doc in store.get_documents()]
    return DocumentListResponse(documents=docs)
