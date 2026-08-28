from app.rag.vectorless_retriever import BM25VectorlessRetriever


def test_retriever_returns_relevant_chunk_first() -> None:
    chunks = [
        {
            "chunk_id": "c1",
            "document_id": "d1",
            "document_name": "policy.md",
            "text": "SLA breach risk must be escalated within 15 minutes.",
            "chunk_index": 0,
            "metadata": {},
            "created_at": "2026-01-01T00:00:00Z",
        },
        {
            "chunk_id": "c2",
            "document_id": "d1",
            "document_name": "policy.md",
            "text": "The cafeteria serves lunch on weekdays.",
            "chunk_index": 1,
            "metadata": {},
            "created_at": "2026-01-01T00:00:00Z",
        },
    ]

    retriever = BM25VectorlessRetriever(chunks)
    results = retriever.retrieve("What is the SLA breach escalation risk policy?", top_k=2)

    assert results
    assert results[0].chunk_id == "c1"
    assert all(result.chunk_id != "c2" for result in results)
