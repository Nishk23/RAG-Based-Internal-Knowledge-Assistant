from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent

load_dotenv(REPO_ROOT / ".env")
load_dotenv(BACKEND_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    app_name: str = "RAG-Based Internal Knowledge Assistant"
    environment: str = os.getenv("ENVIRONMENT", "development")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    chunk_size_words: int = int(os.getenv("CHUNK_SIZE_WORDS", "220"))
    chunk_overlap_words: int = int(os.getenv("CHUNK_OVERLAP_WORDS", "40"))
    default_top_k: int = int(os.getenv("DEFAULT_TOP_K", "5"))
    store_dir: Path = BACKEND_DIR / ".local_store"


settings = Settings()
