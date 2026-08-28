from datetime import UTC, datetime

import pytest

from app.storage.document_store import (
    DocumentNotFoundError,
    DocumentStore,
    DuplicateDocumentError,
)


def _document(document_id: str, tenant_id: str, checksum: str) -> dict[str, object]:
    return {
        "document_id": document_id,
        "tenant_id": tenant_id,
        "document_name": "policy.md",
        "content_type": "text/markdown",
        "checksum": checksum,
        "chunk_count": 1,
        "allowed_roles": ["reader", "admin"],
        "created_by": "user-1",
        "created_at": datetime.now(UTC),
        "metadata": {},
    }


def _chunk(document_id: str, tenant_id: str) -> dict[str, object]:
    return {
        "chunk_id": f"{document_id}_chunk_0",
        "document_id": document_id,
        "tenant_id": tenant_id,
        "document_name": "policy.md",
        "text": "A tenant-scoped policy.",
        "chunk_index": 0,
        "allowed_roles": ["reader", "admin"],
        "created_at": datetime.now(UTC),
        "metadata": {},
    }


def test_store_enforces_tenant_and_role_boundaries(tmp_path) -> None:
    store = DocumentStore(tmp_path)
    store.initialize()
    store.add_document_with_chunks(
        _document("d1", "tenant-a", "a" * 64), [_chunk("d1", "tenant-a")]
    )

    assert len(store.get_chunks("tenant-a", ["reader"])) == 1
    assert store.get_chunks("tenant-b", ["reader"]) == []
    assert store.get_chunks("tenant-a", ["editor"]) == []


def test_store_deduplicates_and_deletes_atomically(tmp_path) -> None:
    store = DocumentStore(tmp_path)
    store.initialize()
    document = _document("d1", "tenant-a", "b" * 64)
    store.add_document_with_chunks(document, [_chunk("d1", "tenant-a")])

    duplicate = _document("d2", "tenant-a", "b" * 64)
    with pytest.raises(DuplicateDocumentError):
        store.add_document_with_chunks(duplicate, [_chunk("d2", "tenant-a")])

    store.delete_document("tenant-a", "d1")
    assert store.get_chunks("tenant-a", ["reader"]) == []
    with pytest.raises(DocumentNotFoundError):
        store.delete_document("tenant-a", "d1")


def test_audit_events_are_tenant_scoped(tmp_path) -> None:
    store = DocumentStore(tmp_path)
    store.initialize()
    store.record_audit_event(
        tenant_id="tenant-a",
        subject="user-1",
        action="knowledge.query",
        resource_type="knowledge_base",
        outcome="success",
        request_id="request-1",
    )
    assert len(store.get_audit_events("tenant-a")) == 1
    assert store.get_audit_events("tenant-b") == []
