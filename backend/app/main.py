from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import routes_chat, routes_documents, routes_evaluation
from app.schemas import HealthResponse

app = FastAPI(
    title="RAG-Based Internal Knowledge Assistant API",
    version="1.0.0",
    description="FastAPI backend for a vectorless RAG system using BM25 retrieval.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_documents.router)
app.include_router(routes_chat.router)
app.include_router(routes_evaluation.router)


@app.get("/health", response_model=HealthResponse, tags=["health"])
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="backend", version="1.0.0")
