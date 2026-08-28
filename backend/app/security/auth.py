from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError, PyJWKClient

from app.config import settings

VALID_ROLES = frozenset({"reader", "editor", "admin"})
bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Principal:
    subject: str
    tenant_id: str
    roles: frozenset[str]

    def has_any_role(self, required: set[str]) -> bool:
        return bool(self.roles & required)


@lru_cache(maxsize=1)
def _jwks_client() -> PyJWKClient:
    if not settings.oidc_jwks_url:
        raise RuntimeError("OIDC_JWKS_URL is not configured")
    return PyJWKClient(settings.oidc_jwks_url, cache_keys=True, lifespan=300)


def _claim_as_roles(value: Any) -> frozenset[str]:
    if isinstance(value, str):
        raw_roles = value.replace(",", " ").split()
    elif isinstance(value, list):
        raw_roles = [str(role) for role in value]
    else:
        raw_roles = []
    return frozenset(role for role in raw_roles if role in VALID_ROLES)


def _decode_oidc_token(token: str) -> Principal:
    try:
        signing_key = _jwks_client().get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=settings.oidc_algorithm_list,
            audience=settings.oidc_audience,
            issuer=settings.oidc_issuer,
            options={"require": ["exp", "iat", "sub"]},
        )
    except (InvalidTokenError, RuntimeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    subject = str(claims.get("sub", "")).strip()
    tenant_id = str(claims.get(settings.oidc_tenant_claim, "")).strip()
    roles = _claim_as_roles(claims.get(settings.oidc_roles_claim))
    if not subject or not tenant_id or not roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token is missing the required tenant or role claims.",
        )
    return Principal(subject=subject, tenant_id=tenant_id, roles=roles)


def get_current_principal(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> Principal:
    if settings.auth_mode == "disabled":
        if settings.environment == "production":
            raise HTTPException(status_code=503, detail="Authentication is misconfigured.")
        principal = Principal(
            subject=settings.dev_subject,
            tenant_id=settings.dev_tenant_id,
            roles=frozenset(settings.development_role_list),
        )
    else:
        if credentials is None or credentials.scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Bearer authentication is required.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        principal = _decode_oidc_token(credentials.credentials)

    request.state.principal = principal
    return principal


def require_roles(*required_roles: str) -> Callable[..., Principal]:
    required = set(required_roles)
    if not required or not required <= VALID_ROLES:
        raise ValueError("At least one valid role is required")

    def dependency(principal: Principal = Depends(get_current_principal)) -> Principal:
        if not principal.has_any_role(required):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for this operation.",
            )
        return principal

    return dependency
