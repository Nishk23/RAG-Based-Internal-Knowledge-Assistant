# Architecture

## Overview

The system is split into a Next.js frontend and a FastAPI backend.

- Frontend handles document upload, query input, source display, and optional evaluation views.
- Backend handles ingestion, chunking, retrieval, orchestration, answer generation, and evaluation.

## Frontend layer

- `src/components/DocumentUpload.tsx`: upload files and trigger sample document loading.
- `src/components/ChatPanel.tsx`: submits questions and displays answers/sources.
- `src/components/EvaluationPanel.tsx`: renders RAGAS metrics when available.
- `src/lib/api.ts`: typed API client layer.

## Backend layer

- `app/api/routes_documents.py`: upload/list/load-sample endpoints.
- `app/api/routes_chat.py`: main RAG query endpoint.
- `app/api/routes_evaluation.py`: explicit evaluation endpoint.
- `app/storage/document_store.py`: JSON-backed local persistence.

## Document ingestion pipeline

1. Parse upload (`.txt`, `.md`, `.pdf`).
2. Normalize text and split into overlapping chunks.
3. Store chunk metadata and text under `backend/.local_store/chunks.json`.

Each stored chunk includes:
- `chunk_id`
- `document_id`
- `document_name`
- `text`
- `chunk_index`
- `metadata`
- `created_at`

## Vectorless retrieval pipeline

Retrieval is lexical-only and embedding-free:

1. Tokenize all chunk text.
2. Build BM25 corpus using `rank-bm25`.
3. Tokenize user query.
4. Rank by BM25 score.
5. Return top-k chunks and scores.

This design is intentionally "vectorless" because no embedding model and no vector index are involved.

## LangGraph workflow

The query flow is implemented as a directed graph:

1. `validate_question`
2. `retrieve_context`
3. `generate_answer`
4. `format_response`
5. `evaluate_answer` (optional)

State keys:
- `question`
- `retrieved_chunks`
- `answer`
- `sources`
- `evaluation`
- `errors`

## RAGAS evaluation

RAGAS evaluates answer quality and retrieval quality (when metrics are available in the installed version):

- `faithfulness`
- `answer_relevancy`
- `context_precision`
- `context_recall`
- `context_relevancy`

The system dynamically checks metric availability. Missing metrics are skipped and logged.

## Limitations

- BM25 retrieval can miss semantic matches with different vocabulary.
- JSON local store is suitable for demos but not high-concurrency production use.
- RAGAS evaluation needs LLM credentials and can increase latency/cost.

## Future improvements

- Add hybrid lexical + lightweight reranking.
- Introduce document deduplication and upsert strategy.
- Add usage analytics and retrieval diagnostics dashboards.
- Add tenant-aware metadata filters.
