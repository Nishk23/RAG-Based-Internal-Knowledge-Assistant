from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import TypedDict

from app.rag.chunker import chunk_text
from app.rag.vectorless_retriever import BM25VectorlessRetriever


class EvaluationCase(TypedDict):
    question: str
    expected_document: str


def build_corpus(sample_dir: Path) -> list[dict[str, object]]:
    corpus: list[dict[str, object]] = []
    for document in sorted(sample_dir.glob("*.md")):
        for index, text in enumerate(chunk_text(document.read_text(), 100, 20)):
            corpus.append(
                {
                    "chunk_id": f"{document.stem}-{index}",
                    "document_id": document.stem,
                    "document_name": document.name,
                    "text": text,
                    "chunk_index": index,
                    "metadata": {},
                    "created_at": "evaluation",
                }
            )
    return corpus


def evaluate(top_k: int) -> dict[str, float | int]:
    backend_dir = Path(__file__).resolve().parents[1]
    cases: list[EvaluationCase] = json.loads(
        (backend_dir / "evaluation" / "golden_dataset.json").read_text()
    )
    retriever = BM25VectorlessRetriever(build_corpus(backend_dir / "sample_docs"))

    hits = 0
    reciprocal_rank_total = 0.0
    for case in cases:
        results = retriever.retrieve(case["question"], top_k=top_k)
        names = [result.document_name for result in results]
        if case["expected_document"] in names:
            hits += 1
            reciprocal_rank_total += 1 / (names.index(case["expected_document"]) + 1)

    total = len(cases)
    return {
        "cases": total,
        "recall_at_k": hits / total if total else 0.0,
        "mrr": reciprocal_rank_total / total if total else 0.0,
        "top_k": top_k,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the deterministic retrieval quality gate.")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--min-recall", type=float, default=0.95)
    parser.add_argument("--min-mrr", type=float, default=0.85)
    args = parser.parse_args()

    report = evaluate(args.top_k)
    print(json.dumps(report, indent=2, sort_keys=True))
    if report["recall_at_k"] < args.min_recall or report["mrr"] < args.min_mrr:
        raise SystemExit("Retrieval quality gate failed.")


if __name__ == "__main__":
    main()
