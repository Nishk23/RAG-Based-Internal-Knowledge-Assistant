import pytest
from pydantic import ValidationError

from app.config import Settings


def test_production_configuration_fails_closed() -> None:
    with pytest.raises(ValidationError, match="Unsafe production configuration"):
        Settings(environment="production", _env_file=None)


def test_development_configuration_parses_security_lists() -> None:
    configured = Settings(
        environment="test",
        cors_origins="https://one.example,https://two.example",
        dev_roles="reader,admin",
        _env_file=None,
    )
    assert configured.cors_origin_list == ["https://one.example", "https://two.example"]
    assert configured.development_role_list == ["reader", "admin"]


def test_complete_production_configuration_is_accepted() -> None:
    configured = Settings(
        environment="production",
        auth_mode="oidc",
        oidc_issuer="https://identity.example.com/",
        oidc_audience="knowledge-assistant-api",
        oidc_jwks_url="https://identity.example.com/.well-known/jwks.json",
        database_url="postgresql+psycopg://service:secret@database/knowledge",
        redis_url="rediss://:secret@redis/0",
        cors_origins="https://knowledge.example.com",
        trusted_hosts="api.knowledge.example.com",
        metrics_bearer_token="metrics-secret",  # noqa: S106 - synthetic test value
        openai_api_key="provider-secret",
        _env_file=None,
    )
    assert configured.environment == "production"


@pytest.mark.parametrize(
    ("database_url", "trusted_hosts"),
    [
        ("mysql://service:secret@database/knowledge", "api.knowledge.example.com"),
        ("postgresql+psycopg://service:secret@database/knowledge", "*"),
    ],
)
def test_production_rejects_unsupported_database_or_wildcard_host(
    database_url: str, trusted_hosts: str
) -> None:
    with pytest.raises(ValidationError, match="Unsafe production configuration"):
        Settings(
            environment="production",
            auth_mode="oidc",
            oidc_issuer="https://identity.example.com/",
            oidc_audience="knowledge-assistant-api",
            oidc_jwks_url="https://identity.example.com/.well-known/jwks.json",
            database_url=database_url,
            redis_url="rediss://:secret@redis/0",
            cors_origins="https://knowledge.example.com",
            trusted_hosts=trusted_hosts,
            metrics_bearer_token="metrics-secret",  # noqa: S106 - synthetic test value
            openai_api_key="provider-secret",
            _env_file=None,
        )
