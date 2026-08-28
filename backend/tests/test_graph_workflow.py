from app.rag import graph


def _chunks() -> list[dict[str, object]]:
    return [
        {
            "chunk_id": "c1",
            "document_id": "d1",
            "document_name": "policy.md",
            "text": "SLA incidents require updates every 30 minutes.",
            "chunk_index": 0,
            "metadata": {},
            "created_at": "2026-01-01T00:00:00Z",
        }
    ]


def test_complete_graph_workflow_with_evaluation(monkeypatch) -> None:
    monkeypatch.setattr(
        graph,
        "generate_answer",
        lambda _question, _chunks: "Updates are required every 30 minutes [1].",
    )
    result = graph.run_rag_workflow(
        question="  When are SLA incident updates required?  ",
        all_chunks=_chunks(),
        top_k=5,
        evaluate=True,
    )

    assert result["question"] == "When are SLA incident updates required?"
    assert result["sources"][0]["citation_index"] == 1
    assert result["evaluation"]["status"] == "success"


def test_graph_stops_after_invalid_question() -> None:
    result = graph.run_rag_workflow(
        question="   ",
        all_chunks=_chunks(),
        top_k=5,
        evaluate=False,
    )
    assert result["errors"] == ["Question is empty."]


def test_evaluation_failure_is_returned_as_structured_state(monkeypatch) -> None:
    def fail_evaluation(**_kwargs):
        raise RuntimeError("evaluation failed")

    monkeypatch.setattr(graph, "run_quality_evaluation", fail_evaluation)
    result = graph.evaluate_answer(
        {
            "question": "question",
            "answer": "answer",
            "retrieved_chunks": [],
            "evaluate": True,
        }
    )
    assert result["evaluation"]["status"] == "error"


def test_query_cleanup_normalizes_whitespace() -> None:
    assert graph.query_cleanup("  a   b  ") == "a b"
