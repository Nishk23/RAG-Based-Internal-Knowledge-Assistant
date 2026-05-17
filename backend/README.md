# Backend

FastAPI backend for the RAG-Based Internal Knowledge Assistant.

## Features

- Document ingestion for `.txt`, `.md`, `.pdf`
- Configurable chunking with overlap
- **Vectorless retrieval** using BM25 (no embeddings, no vector DB)
- LangGraph workflow orchestration
- LangChain LLM answer generation with OpenAI fallback messaging
- Optional RAGAS evaluation endpoint

## Run locally

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Run tests

```bash
cd backend
pytest -q
```
