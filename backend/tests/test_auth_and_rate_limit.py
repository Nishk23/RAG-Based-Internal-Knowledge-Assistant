from datetime import UTC, datetime, timedelta

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException

from app.config import settings
from app.security import auth
from app.security.auth import Principal, _claim_as_roles, _decode_oidc_token, require_roles
from app.security.rate_limit import RateLimiter


class _SigningKey:
    def __init__(self, key: object) -> None:
        self.key = key


class _StaticJwksClient:
    def __init__(self, key: object) -> None:
        self.key = key

    def get_signing_key_from_jwt(self, _: str) -> _SigningKey:
        return _SigningKey(self.key)


def _signed_token(private_key: object, **overrides: object) -> str:
    now = datetime.now(UTC)
    claims: dict[str, object] = {
        "sub": "user-1",
        "iss": "https://identity.example.com/",
        "aud": "knowledge-assistant-api",
        "iat": now,
        "exp": now + timedelta(minutes=5),
        "tenant_id": "tenant-a",
        "roles": ["reader"],
    }
    claims.update(overrides)
    return jwt.encode(claims, private_key, algorithm="RS256")


def test_role_claim_normalization_ignores_unknown_roles() -> None:
    assert _claim_as_roles("reader,unknown admin") == frozenset({"reader", "admin"})
    assert _claim_as_roles(["editor", "invalid"]) == frozenset({"editor"})
    assert _claim_as_roles(None) == frozenset()


def test_role_dependency_denies_insufficient_role() -> None:
    dependency = require_roles("admin")
    with pytest.raises(HTTPException) as error:
        dependency(Principal("user", "tenant", frozenset({"reader"})))
    assert error.value.status_code == 403


def test_in_memory_rate_limit(monkeypatch) -> None:
    monkeypatch.setattr(settings, "redis_url", None)
    monkeypatch.setattr(settings, "rate_limit_window_seconds", 60)
    limiter = RateLimiter()
    assert limiter.consume("key", 1)[0] is True
    assert limiter.consume("key", 1)[0] is False
    assert limiter.healthcheck() is True


def test_oidc_decoder_verifies_signature_and_claims(monkeypatch) -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    monkeypatch.setattr(auth, "_jwks_client", lambda: _StaticJwksClient(private_key.public_key()))
    monkeypatch.setattr(settings, "oidc_issuer", "https://identity.example.com/")
    monkeypatch.setattr(settings, "oidc_audience", "knowledge-assistant-api")

    principal = _decode_oidc_token(_signed_token(private_key))

    assert principal == Principal("user-1", "tenant-a", frozenset({"reader"}))


def test_oidc_decoder_rejects_wrong_audience(monkeypatch) -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    monkeypatch.setattr(auth, "_jwks_client", lambda: _StaticJwksClient(private_key.public_key()))
    monkeypatch.setattr(settings, "oidc_issuer", "https://identity.example.com/")
    monkeypatch.setattr(settings, "oidc_audience", "knowledge-assistant-api")

    with pytest.raises(HTTPException) as error:
        _decode_oidc_token(_signed_token(private_key, aud="different-service"))
    assert error.value.status_code == 401


def test_oidc_decoder_requires_tenant_and_recognized_roles(monkeypatch) -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    monkeypatch.setattr(auth, "_jwks_client", lambda: _StaticJwksClient(private_key.public_key()))
    monkeypatch.setattr(settings, "oidc_issuer", "https://identity.example.com/")
    monkeypatch.setattr(settings, "oidc_audience", "knowledge-assistant-api")

    with pytest.raises(HTTPException) as error:
        _decode_oidc_token(_signed_token(private_key, tenant_id="", roles=["unknown"]))
    assert error.value.status_code == 403
