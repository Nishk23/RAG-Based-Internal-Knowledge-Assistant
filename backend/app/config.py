from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    """Validated runtime configuration with fail-closed production defaults."""

    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Enterprise Internal Knowledge Assistant"
    environment: Literal["development", "test", "production"] = "development"
    log_level: str = "INFO"

    database_url: str = f"sqlite:///{BACKEND_DIR / '.local_store' / 'knowledge.db'}"
    database_pool_size: int = Field(default=10, ge=1, le=100)
    database_max_overflow: int = Field(default=20, ge=0, le=200)

    auth_mode: Literal["disabled", "oidc"] = "disabled"
    oidc_issuer: str | None = None
    oidc_audience: str | None = None
    oidc_jwks_url: str | None = None
    oidc_algorithms: str = "RS256"
    oidc_roles_claim: str = "roles"
    oidc_tenant_claim: str = "tenant_id"
    dev_subject: str = "local-admin"
    dev_tenant_id: str = "local"
    dev_roles: str = "reader,editor,admin"

    cors_origins: str = "http://localhost:3000"
    trusted_hosts: str = "localhost,127.0.0.1,testserver"
    metrics_bearer_token: SecretStr | None = None

    openai_api_key: SecretStr | None = None
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str | None = None
    llm_timeout_seconds: float = Field(default=30.0, ge=1.0, le=180.0)
    llm_max_retries: int = Field(default=2, ge=0, le=5)

    chunk_size_words: int = Field(default=220, ge=50, le=2000)
    chunk_overlap_words: int = Field(default=40, ge=0, le=500)
    default_top_k: int = Field(default=5, ge=1, le=20)
    retrieval_min_score: float = Field(default=0.05, ge=0.0)
    retrieval_min_relative_score: float = Field(default=0.20, ge=0.0, le=1.0)

    max_upload_bytes: int = Field(default=10 * 1024 * 1024, ge=1024)
    max_pdf_pages: int = Field(default=250, ge=1, le=5000)
    max_extracted_characters: int = Field(default=2_000_000, ge=1000)
    clamav_host: str | None = None
    clamav_port: int = Field(default=3310, ge=1, le=65535)
    require_malware_scan: bool = False

    redis_url: str | None = None
    rate_limit_window_seconds: int = Field(default=60, ge=1, le=3600)
    rate_limit_default: int = Field(default=120, ge=1)
    rate_limit_chat: int = Field(default=20, ge=1)
    rate_limit_upload: int = Field(default=10, ge=1)
    rate_limit_evaluation: int = Field(default=10, ge=1)

    otel_exporter_otlp_endpoint: str | None = None
    otel_service_name: str = "rag-knowledge-assistant"

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        normalized = value.upper()
        if normalized not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError("LOG_LEVEL must be a valid Python logging level")
        return normalized

    @model_validator(mode="after")
    def validate_runtime_safety(self) -> Settings:
        if self.chunk_overlap_words >= self.chunk_size_words:
            raise ValueError("CHUNK_OVERLAP_WORDS must be smaller than CHUNK_SIZE_WORDS")
        if self.require_malware_scan and not self.clamav_host:
            raise ValueError("CLAMAV_HOST is required when REQUIRE_MALWARE_SCAN=true")

        if self.environment == "production":
            missing: list[str] = []
            if self.auth_mode != "oidc":
                missing.append("AUTH_MODE=oidc")
            for name, value in (
                ("OIDC_ISSUER", self.oidc_issuer),
                ("OIDC_AUDIENCE", self.oidc_audience),
                ("OIDC_JWKS_URL", self.oidc_jwks_url),
                ("REDIS_URL", self.redis_url),
                ("METRICS_BEARER_TOKEN", self.metrics_bearer_token),
                ("OPENAI_API_KEY", self.openai_api_key),
            ):
                if not value:
                    missing.append(name)
            if not self.database_url.startswith(("postgresql://", "postgresql+psycopg://")):
                missing.append("a PostgreSQL DATABASE_URL")
            if "*" in self.cors_origin_list:
                missing.append("explicit CORS_ORIGINS")
            if not self.trusted_host_list or "*" in self.trusted_host_list:
                missing.append("explicit TRUSTED_HOSTS")
            if missing:
                raise ValueError(
                    "Unsafe production configuration; configure: " + ", ".join(missing)
                )
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [value.strip() for value in self.cors_origins.split(",") if value.strip()]

    @property
    def trusted_host_list(self) -> list[str]:
        return [value.strip() for value in self.trusted_hosts.split(",") if value.strip()]

    @property
    def oidc_algorithm_list(self) -> list[str]:
        return [value.strip() for value in self.oidc_algorithms.split(",") if value.strip()]

    @property
    def development_role_list(self) -> list[str]:
        return [value.strip() for value in self.dev_roles.split(",") if value.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
