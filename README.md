# RAG-Based Internal Knowledge Assistant

A production-style portfolio project implementing a **vectorless RAG** system for internal knowledge search and Q&A.

This app demonstrates:
- Next.js + React + TypeScript frontend
- FastAPI backend
- LangChain prompt orchestration
- LangGraph workflow graph
- BM25 lexical retrieval (no vector DB, no embeddings)
- RAGAS-based quality evaluation
- Dockerized local development

## Why this project stands out

This repository is intentionally built to support resume claims such as:

> Built a configurable RAG system with LangChain for internal datasets and evaluated answer relevance, faithfulness, hallucination risk, and retrieval quality using RAGAS.

## Architecture (text diagram)

```text
[Frontend: Next.js Dashboard]
        |
        | HTTP (upload, chat, evaluate)
        v
[Backend: FastAPI]
  ├─ /documents/upload, /documents/load-sample
  ├─ /chat
  ├─ /evaluate
  └─ /health
        |
        v
[Ingestion Pipeline]
  file parser (.txt/.md/.pdf) -> chunker -> JSON local store (.local_store)
        |
        v
[Vectorless Retrieval]
  BM25 over lexical tokens (rank-bm25)
        |
        v
[LangGraph RAG Workflow]
  validate_question -> retrieve_context -> generate_answer -> format_response -> evaluate_answer(optional)
        |
        v
[LangChain + ChatOpenAI]
  prompt templating + LLM generation (with missing-key fallback)
        |
        v
[RAGAS]
  faithfulness, answer_relevancy, context_precision, context_recall, context_relevancy (if available)
```

## Features

- Upload `.txt`, `.md`, `.pdf` documents
- Load bundled sample documents in one click
- Chunking with configurable size/overlap
- BM25 sparse retrieval with chunk scoring
- Source-grounded answers with chunk citations
- Optional RAGAS quality scoring
- Structured backend logging
- Pytest coverage for chunking, retrieval, and health endpoint

## Tech stack

- Frontend: Next.js 14, React 18, TypeScript, Tailwind CSS
- Backend: FastAPI, Pydantic
- RAG orchestration: LangChain, LangGraph
- Retrieval: rank-bm25 (vectorless lexical retrieval)
- Evaluation: RAGAS + datasets + pandas
- Infra: Docker Compose

## Vectorless RAG explanation

This system intentionally avoids embeddings and vector databases.

Retrieval uses BM25 (term frequency/inverse document frequency family). Query and chunk text are tokenized and matched lexically. This is a sparse retrieval design that is transparent, lightweight, and easy to audit for internal knowledge workflows.

See [vectorless_rag.md](/Users/nishanthnarayanan/Documents/Codex/2026-05-17/you-are-acting-as-a-senior/rag-internal-knowledge-assistant/docs/vectorless_rag.md).

## LangGraph workflow

The RAG graph has these nodes:

1. `validate_question`
2. `retrieve_context`
3. `generate_answer`
4. `format_response`
5. `evaluate_answer` (optional)

The graph state tracks question, retrieved chunks, answer, sources, evaluation results, and errors.

## RAGAS evaluation

`/evaluate` and optional `/chat` evaluation compute available RAGAS metrics. The implementation gracefully handles version differences:

- Missing metrics are skipped with warnings.
- If `OPENAI_API_KEY` is missing, evaluation returns a clear error message.

See [ragas_evaluation.md](/Users/nishanthnarayanan/Documents/Codex/2026-05-17/you-are-acting-as-a-senior/rag-internal-knowledge-assistant/docs/ragas_evaluation.md).

## Repository structure

```text
rag-internal-knowledge-assistant/
  backend/
  frontend/
  docs/
  docker-compose.yml
  .env.example
  .gitignore
  README.md
```

## Setup

1. Clone repository.
2. Copy env file.

```bash
cp .env.example .env
```

3. Add `OPENAI_API_KEY` in `.env` if you want LLM answer generation and RAGAS metrics.

## Local development (without Docker)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Docker development

```bash
docker compose up --build
```

- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend: [http://localhost:8000](http://localhost:8000)

## API examples

### Health

```bash
curl http://localhost:8000/health
```

### Upload document

```bash
curl -X POST http://localhost:8000/documents/upload \
  -F "file=@backend/sample_docs/sla_operations.md"
```

### Load sample docs

```bash
curl -X POST http://localhost:8000/documents/load-sample
```

### Ask question

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What does the SLA policy say about breach risk?",
    "top_k": 5,
    "evaluate": false
  }'
```

### Run evaluation

```bash
curl -X POST http://localhost:8000/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the SLA update cadence for Sev-1?",
    "answer": "Status updates must be posted every 30 minutes.",
    "contexts": ["Status updates must be posted every 30 minutes during active mitigation."]
  }'
```
