from __future__ import annotations

import contextvars
import json
import logging
from datetime import UTC, datetime
from typing import Any

from app.config import settings

request_id_context: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_context.get(),
        }
        reserved = set(logging.makeLogRecord({}).__dict__) | {"message", "asctime"}
        extras = {
            key: value
            for key, value in record.__dict__.items()
            if key not in reserved and not key.startswith("_")
        }
        if extras:
            payload["extra"] = extras
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str, ensure_ascii=False)


def configure_logging() -> None:
    root = logging.getLogger()
    root.handlers.clear()
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)
    root.setLevel(settings.log_level)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
