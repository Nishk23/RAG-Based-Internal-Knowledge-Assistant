from __future__ import annotations

import re
import secrets
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.middleware.base import RequestResponseEndpoint

from app.api import routes_audit, routes_chat, routes_documents, routes_evaluation
from app.config import settings
from app.dependencies import store
from app.observability import (
    HTTP_DURATION,
    HTTP_IN_PROGRESS,
    HTTP_REQUESTS,
    configure_telemetry,
)
from app.schemas import HealthResponse, PrincipalResponse, ReadinessResponse
from app.security.auth import Principal, require_roles
from app.security.rate_limit import limiter
from app.utils.logging import configure_logging, get_logger, request_id_context

APP_VERSION = "1.0.1"
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,128}$")

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    if settings.environment != "production":
        store.initialize()
    else:
        store.healthcheck()
    logger.info("application_started", extra={"version": APP_VERSION})
    yield
    logger.info("application_stopped", extra={"version": APP_VERSION})


app = FastAPI(
    title="Enterprise Internal Knowledge Assistant API",
    version=APP_VERSION,
    description="Tenant-isolated, access-controlled internal knowledge retrieval API.",
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url=None,
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_host_list)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
)


@app.middleware("http")
async def request_context_and_metrics(
    request: Request, call_next: RequestResponseEndpoint
) -> Response:
    supplied_request_id = request.headers.get("X-Request-ID", "")
    request_id = (
        supplied_request_id if REQUEST_ID_PATTERN.fullmatch(supplied_request_id) else str(uuid4())
    )
    request.state.request_id = request_id
    token = request_id_context.set(request_id)
    started = time.perf_counter()
    HTTP_IN_PROGRESS.labels(method=request.method).inc()
    try:
        response = await call_next(request)
    finally:
        HTTP_IN_PROGRESS.labels(method=request.method).dec()
        request_id_context.reset(token)

    route = getattr(request.scope.get("route"), "path", "unmatched")
    duration = time.perf_counter() - started
    HTTP_REQUESTS.labels(method=request.method, route=route, status=str(response.status_code)).inc()
    HTTP_DURATION.labels(method=request.method, route=route).observe(duration)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
    return response


@app.exception_handler(Exception)
async def unexpected_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled_request_error")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Unexpected server error.",
            "request_id": getattr(request.state, "request_id", "unknown"),
        },
    )


app.include_router(routes_documents.router)
app.include_router(routes_chat.router)
app.include_router(routes_evaluation.router)
app.include_router(routes_audit.router)


@app.get("/health", response_model=HealthResponse, tags=["health"])
@app.get("/health/live", response_model=HealthResponse, tags=["health"])
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="backend", version=APP_VERSION)


@app.get("/health/ready", response_model=ReadinessResponse, tags=["health"])
def readiness() -> ReadinessResponse:
    checks: dict[str, str] = {}
    try:
        store.healthcheck()
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "error"
    checks["rate_limit_store"] = "ok" if limiter.healthcheck() else "error"
    if "error" in checks.values():
        raise HTTPException(status_code=503, detail={"status": "not-ready", "checks": checks})
    return ReadinessResponse(status="ready", checks=checks)


@app.get("/me", response_model=PrincipalResponse, tags=["identity"])
def who_am_i(
    principal: Principal = Depends(require_roles("reader", "editor", "admin")),
) -> PrincipalResponse:
    return PrincipalResponse(
        subject=principal.subject,
        tenant_id=principal.tenant_id,
        roles=sorted(principal.roles),
    )


@app.get("/metrics", include_in_schema=False)
def metrics(request: Request) -> Response:
    expected = settings.metrics_bearer_token
    if expected:
        authorization = request.headers.get("Authorization", "")
        supplied = authorization.removeprefix("Bearer ")
        if not secrets.compare_digest(supplied, expected.get_secret_value()):
            raise HTTPException(status_code=401, detail="Metrics authentication required.")
    elif settings.environment == "production":
        raise HTTPException(status_code=503, detail="Metrics authentication is misconfigured.")
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


configure_telemetry(app)
