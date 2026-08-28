from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from sqlalchemy import create_engine, delete, select, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.storage.database import AuditEventModel, Base, ChunkModel, DocumentModel


class DuplicateDocumentError(ValueError):
    pass


class DocumentNotFoundError(ValueError):
    pass


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.isoformat()


def _roles_intersect(allowed_roles: Iterable[str], principal_roles: Iterable[str]) -> bool:
    return bool(set(allowed_roles) & set(principal_roles))


class DocumentStore:
    """Transactional document, chunk, and audit persistence.

    SQLite is supported for local development and tests. Production settings
    fail closed unless a PostgreSQL URL is supplied.
    """

    def __init__(self, database_url: str | Path | None = None) -> None:
        if isinstance(database_url, Path):
            database_url.mkdir(parents=True, exist_ok=True)
            database_url = f"sqlite:///{database_url / 'knowledge.db'}"
        self.database_url = str(database_url or settings.database_url)
        if self.database_url.startswith("sqlite"):
            sqlite_database = make_url(self.database_url).database
            if sqlite_database and sqlite_database != ":memory:":
                Path(sqlite_database).parent.mkdir(parents=True, exist_ok=True)
        connect_args = (
            {"check_same_thread": False, "timeout": 30}
            if self.database_url.startswith("sqlite")
            else {}
        )
        engine_kwargs: dict[str, Any] = {
            "pool_pre_ping": True,
            "connect_args": connect_args,
        }
        if not self.database_url.startswith("sqlite"):
            engine_kwargs.update(
                pool_size=settings.database_pool_size,
                max_overflow=settings.database_max_overflow,
            )
        self.engine: Engine = create_engine(self.database_url, **engine_kwargs)
        self.session_factory = sessionmaker(
            bind=self.engine, class_=Session, expire_on_commit=False
        )

    def initialize(self) -> None:
        Base.metadata.create_all(self.engine)

    def healthcheck(self) -> bool:
        with self.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True

    def add_document_with_chunks(
        self,
        document: dict[str, Any],
        chunks: list[dict[str, Any]],
    ) -> None:
        model = DocumentModel(
            document_id=document["document_id"],
            tenant_id=document["tenant_id"],
            document_name=document["document_name"],
            content_type=document["content_type"],
            checksum=document["checksum"],
            chunk_count=document["chunk_count"],
            allowed_roles=document["allowed_roles"],
            created_by=document["created_by"],
            created_at=document["created_at"],
            metadata_json=document.get("metadata", {}),
        )
        chunk_models = [
            ChunkModel(
                chunk_id=chunk["chunk_id"],
                document_id=chunk["document_id"],
                tenant_id=chunk["tenant_id"],
                document_name=chunk["document_name"],
                text=chunk["text"],
                chunk_index=chunk["chunk_index"],
                allowed_roles=chunk["allowed_roles"],
                created_at=chunk["created_at"],
                metadata_json=chunk.get("metadata", {}),
            )
            for chunk in chunks
        ]
        try:
            with self.session_factory.begin() as session:
                session.add(model)
                session.add_all(chunk_models)
        except IntegrityError as exc:
            raise DuplicateDocumentError(
                "An identical document already exists in this tenant."
            ) from exc

    def get_documents(self, tenant_id: str, roles: Iterable[str]) -> list[dict[str, Any]]:
        with self.session_factory() as session:
            records = session.scalars(
                select(DocumentModel)
                .where(DocumentModel.tenant_id == tenant_id)
                .order_by(DocumentModel.created_at.desc())
            ).all()
        return [
            {
                "document_id": record.document_id,
                "document_name": record.document_name,
                "chunk_count": record.chunk_count,
                "created_at": _iso(record.created_at),
                "allowed_roles": record.allowed_roles,
                "metadata": record.metadata_json,
            }
            for record in records
            if _roles_intersect(record.allowed_roles, roles)
        ]

    def get_chunks(
        self,
        tenant_id: str,
        roles: Iterable[str],
        document_id: str | None = None,
    ) -> list[dict[str, Any]]:
        statement = select(ChunkModel).where(ChunkModel.tenant_id == tenant_id)
        if document_id:
            statement = statement.where(ChunkModel.document_id == document_id)
        with self.session_factory() as session:
            records = session.scalars(statement.order_by(ChunkModel.chunk_id)).all()
        return [
            {
                "chunk_id": record.chunk_id,
                "document_id": record.document_id,
                "tenant_id": record.tenant_id,
                "document_name": record.document_name,
                "text": record.text,
                "chunk_index": record.chunk_index,
                "allowed_roles": record.allowed_roles,
                "metadata": record.metadata_json,
                "created_at": _iso(record.created_at),
            }
            for record in records
            if _roles_intersect(record.allowed_roles, roles)
        ]

    def delete_document(self, tenant_id: str, document_id: str) -> None:
        with self.session_factory.begin() as session:
            document = session.scalar(
                select(DocumentModel).where(
                    DocumentModel.tenant_id == tenant_id,
                    DocumentModel.document_id == document_id,
                )
            )
            if document is None:
                raise DocumentNotFoundError("Document not found.")
            session.execute(delete(ChunkModel).where(ChunkModel.document_id == document_id))
            session.delete(document)

    def record_audit_event(
        self,
        *,
        tenant_id: str,
        subject: str,
        action: str,
        resource_type: str,
        outcome: str,
        request_id: str | None,
        resource_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        event = AuditEventModel(
            event_id=str(uuid4()),
            tenant_id=tenant_id,
            subject=subject,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            outcome=outcome,
            request_id=request_id,
            metadata_json=metadata or {},
        )
        with self.session_factory.begin() as session:
            session.add(event)

    def get_audit_events(self, tenant_id: str, limit: int = 100) -> list[dict[str, Any]]:
        with self.session_factory() as session:
            records = session.scalars(
                select(AuditEventModel)
                .where(AuditEventModel.tenant_id == tenant_id)
                .order_by(AuditEventModel.created_at.desc())
                .limit(limit)
            ).all()
        return [
            {
                "event_id": record.event_id,
                "subject": record.subject,
                "action": record.action,
                "resource_type": record.resource_type,
                "resource_id": record.resource_id,
                "outcome": record.outcome,
                "request_id": record.request_id,
                "metadata": record.metadata_json,
                "created_at": _iso(record.created_at),
            }
            for record in records
        ]
