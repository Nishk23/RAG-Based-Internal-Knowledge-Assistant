from __future__ import annotations

from fastapi import FastAPI
from prometheus_client import Counter, Gauge, Histogram

HTTP_REQUESTS = Counter(
    "rag_http_requests_total",
    "HTTP requests handled by the API.",
    ("method", "route", "status"),
)
HTTP_DURATION = Histogram(
    "rag_http_request_duration_seconds",
    "HTTP request duration in seconds.",
    ("method", "route"),
)
HTTP_IN_PROGRESS = Gauge(
    "rag_http_requests_in_progress",
    "HTTP requests currently being processed.",
    ("method",),
)


def configure_telemetry(app: FastAPI) -> None:
    from app.config import settings

    if not settings.otel_exporter_otlp_endpoint:
        return

    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    provider = TracerProvider(
        resource=Resource.create({"service.name": settings.otel_service_name})
    )
    exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app, excluded_urls="health/live,health/ready,metrics")
