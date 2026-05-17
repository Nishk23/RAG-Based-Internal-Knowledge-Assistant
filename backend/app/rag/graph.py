from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.config import settings
from app.evaluation.ragas_runner import run_ragas_evaluation
from app.rag.rag_chain import generate_answer
from app.rag.vectorless_retriever import BM25VectorlessRetriever
from app.utils.logging import get_logger

logger = get_logger(__name__)


class RAGState(TypedDict, total=False):
    question: str
    top_k: int
    evaluate: bool
    all_chunks: list[dict[str, Any]]
    retrieved_chunks: list[dict[str, Any]]
    answer: str
    sources: list[dict[str, Any]]
    evaluation: dict[str, Any] | None
    errors: list[str]


def validate_question(state: RAGState) -> RAGState:
    question = (state.get("question") or "").strip()
    if not question:
        errors = state.get("errors", [])
        errors.append("Question is empty.")
        return {"errors": errors}
    return {"question": question}


def retrieve_context(state: RAGState) -> RAGState:
    question = state.get("question", "")
    top_k = state.get("top_k", settings.default_top_k)
    chunks = state.get("all_chunks", [])

    retriever = BM25VectorlessRetriever(chunks)
    retrieved = retriever.retrieve(question=query_cleanup(question), top_k=top_k)

    retrieved_dicts = [chunk.__dict__ for chunk in retrieved]
    logger.info(
        "retrieval_completed",
        extra={"question": question, "top_k": top_k, "retrieved": len(retrieved_dicts)},
    )
    return {"retrieved_chunks": retrieved_dicts}


def generate_answer_node(state: RAGState) -> RAGState:
    question = state.get("question", "")
    retrieved_chunks = state.get("retrieved_chunks", [])
    answer = generate_answer(question, retrieved_chunks)
    logger.info("answer_generated", extra={"question": question, "answer_length": len(answer)})
    return {"answer": answer}


def format_response(state: RAGState) -> RAGState:
    sources = [
        {
            "document_name": c.get("document_name", ""),
            "chunk_id": c.get("chunk_id", ""),
            "text": c.get("text", ""),
            "score": float(c.get("score", 0.0)),
        }
        for c in state.get("retrieved_chunks", [])
    ]
    return {"sources": sources}


def evaluate_answer(state: RAGState) -> RAGState:
    if not state.get("evaluate", False):
        return {"evaluation": None}

    try:
        report = run_ragas_evaluation(
            question=state.get("question", ""),
            answer=state.get("answer", ""),
            contexts=[c.get("text", "") for c in state.get("retrieved_chunks", [])],
            ground_truth=None,
        )
        logger.info("evaluation_completed", extra={"status": report.get("status")})
        return {"evaluation": report}
    except Exception as exc:  # noqa: BLE001
        logger.warning("evaluation_failed", extra={"error": str(exc)})
        return {
            "evaluation": {
                "status": "error",
                "metrics": {},
                "skipped_metrics": [],
                "message": str(exc),
            }
        }


def query_cleanup(question: str) -> str:
    return " ".join(question.strip().split())


def build_graph():
    workflow = StateGraph(RAGState)
    workflow.add_node("validate_question", validate_question)
    workflow.add_node("retrieve_context", retrieve_context)
    workflow.add_node("generate_answer", generate_answer_node)
    workflow.add_node("format_response", format_response)
    workflow.add_node("evaluate_answer", evaluate_answer)

    workflow.add_edge(START, "validate_question")
    workflow.add_edge("validate_question", "retrieve_context")
    workflow.add_edge("retrieve_context", "generate_answer")
    workflow.add_edge("generate_answer", "format_response")
    workflow.add_edge("format_response", "evaluate_answer")
    workflow.add_edge("evaluate_answer", END)

    return workflow.compile()


def run_rag_workflow(
    *,
    question: str,
    all_chunks: list[dict[str, Any]],
    top_k: int,
    evaluate: bool,
) -> RAGState:
    graph = build_graph()
    return graph.invoke(
        {
            "question": question,
            "all_chunks": all_chunks,
            "top_k": top_k,
            "evaluate": evaluate,
            "errors": [],
        }
    )
