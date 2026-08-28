from fastapi.testclient import TestClient

from app.api import routes_audit, routes_chat, routes_documents, routes_evaluation
from app.main import app
from app.storage.document_store import DocumentStore


def _patch_route_stores(monkeypatch, tmp_path) -> DocumentStore:
    test_store = DocumentStore(tmp_path)
    test_store.initialize()
    for module in (routes_audit, routes_chat, routes_documents, routes_evaluation):
        monkeypatch.setattr(module, "store", test_store)
    return test_store


def test_document_lifecycle_and_audit_api(monkeypatch, tmp_path) -> None:
    _patch_route_stores(monkeypatch, tmp_path)
    with TestClient(app) as client:
        upload = client.post(
            "/documents/upload",
            files={
                "file": ("policy.md", b"Escalate incidents within 15 minutes.", "text/markdown")
            },
            data={"allowed_roles": "reader,admin"},
        )
        assert upload.status_code == 201
        document_id = upload.json()["document_id"]
        assert len(upload.json()["checksum"]) == 64

        duplicate = client.post(
            "/documents/upload",
            files={"file": ("copy.md", b"Escalate incidents within 15 minutes.", "text/markdown")},
        )
        assert duplicate.status_code == 409

        listing = client.get("/documents")
        assert listing.status_code == 200
        assert listing.json()["documents"][0]["allowed_roles"] == ["admin", "reader"]

        deletion = client.delete(f"/documents/{document_id}")
        assert deletion.status_code == 200
        assert client.delete(f"/documents/{document_id}").status_code == 404

        audit = client.get("/audit-events")
        assert audit.status_code == 200
        assert {event["action"] for event in audit.json()["events"]} >= {
            "document.upload",
            "document.delete",
        }


def test_upload_rejection_is_audited(monkeypatch, tmp_path) -> None:
    store = _patch_route_stores(monkeypatch, tmp_path)
    with TestClient(app) as client:
        response = client.post(
            "/documents/upload",
            files={"file": ("malformed.pdf", b"not-pdf", "application/pdf")},
        )
    assert response.status_code == 400
    assert store.get_audit_events("local")[0]["outcome"] == "rejected"


def test_chat_and_evaluation_apis(monkeypatch, tmp_path) -> None:
    _patch_route_stores(monkeypatch, tmp_path)
    with TestClient(app) as client:
        client.post(
            "/documents/upload",
            files={"file": ("policy.md", b"Updates occur every 30 minutes.", "text/markdown")},
        )

        monkeypatch.setattr(
            routes_chat,
            "run_rag_workflow",
            lambda **_: {
                "answer": "Updates occur every 30 minutes [1].",
                "sources": [
                    {
                        "citation_index": 1,
                        "document_name": "policy.md",
                        "chunk_id": "chunk-1",
                        "text": "Updates occur every 30 minutes.",
                        "score": 1.0,
                    }
                ],
                "evaluation": None,
                "errors": [],
            },
        )
        chat = client.post("/chat", json={"question": "When are updates?", "top_k": 5})
        assert chat.status_code == 200
        assert chat.json()["sources"][0]["citation_index"] == 1

        evaluation = client.post(
            "/evaluate",
            json={
                "question": "When are updates?",
                "answer": "Every 30 minutes [1].",
                "contexts": ["Updates occur every 30 minutes."],
            },
        )
        assert evaluation.status_code == 200
        assert evaluation.json()["metrics"]["citation_validity"] == 1.0


def test_sample_loader_skips_existing_checksums(monkeypatch, tmp_path) -> None:
    _patch_route_stores(monkeypatch, tmp_path)
    with TestClient(app) as client:
        first = client.post("/documents/load-sample")
        second = client.post("/documents/load-sample")
    assert first.status_code == 200
    assert first.json()["documents_loaded"] > 0
    assert second.json()["documents_loaded"] == 0
