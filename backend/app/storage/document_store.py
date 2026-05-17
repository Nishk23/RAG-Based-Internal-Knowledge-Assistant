from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class DocumentStore:
    """Simple JSON-backed storage for documents and chunks.

    This keeps local development easy and transparent without adding external infrastructure.
    """

    def __init__(self, store_dir: Path) -> None:
        self.store_dir = store_dir
        self.documents_file = self.store_dir / "documents.json"
        self.chunks_file = self.store_dir / "chunks.json"
        self.store_dir.mkdir(parents=True, exist_ok=True)

        if not self.documents_file.exists():
            self._write_json(self.documents_file, [])
        if not self.chunks_file.exists():
            self._write_json(self.chunks_file, [])

    def _read_json(self, path: Path) -> list[dict[str, Any]]:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, list):
            return []
        return data

    def _write_json(self, path: Path, data: list[dict[str, Any]]) -> None:
        with path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)

    def add_document(self, document: dict[str, Any]) -> None:
        docs = self._read_json(self.documents_file)
        docs.append(document)
        self._write_json(self.documents_file, docs)

    def add_chunks(self, chunks: list[dict[str, Any]]) -> None:
        current = self._read_json(self.chunks_file)
        current.extend(chunks)
        self._write_json(self.chunks_file, current)

    def get_documents(self) -> list[dict[str, Any]]:
        return self._read_json(self.documents_file)

    def get_chunks(self, document_id: str | None = None) -> list[dict[str, Any]]:
        chunks = self._read_json(self.chunks_file)
        if document_id is None:
            return chunks
        return [chunk for chunk in chunks if chunk.get("document_id") == document_id]
