from __future__ import annotations

import threading
import time
from collections import defaultdict
from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, status
from redis import Redis
from redis.exceptions import RedisError

from app.config import settings
from app.security.auth import Principal, get_current_principal
from app.utils.logging import get_logger

logger = get_logger(__name__)


class RateLimiter:
    def __init__(self) -> None:
        self._redis = (
            Redis.from_url(settings.redis_url, decode_responses=True)
            if settings.redis_url
            else None
        )
        self._memory: dict[str, tuple[int, int]] = defaultdict(lambda: (0, 0))
        self._lock = threading.Lock()

    def consume(self, key: str, limit: int) -> tuple[bool, int]:
        window = settings.rate_limit_window_seconds
        bucket = int(time.time() // window)
        retry_after = window - int(time.time() % window)
        redis_key = f"rag:ratelimit:{bucket}:{key}"

        if self._redis is not None:
            try:
                with self._redis.pipeline() as pipeline:
                    pipeline.incr(redis_key)
                    pipeline.expire(redis_key, window + 5)
                    count, _ = pipeline.execute()
                return int(count) <= limit, retry_after
            except RedisError:
                logger.exception("rate_limit_redis_error")
                if settings.environment == "production":
                    return False, retry_after

        with self._lock:
            existing_bucket, count = self._memory[key]
            if existing_bucket != bucket:
                count = 0
            count += 1
            self._memory[key] = (bucket, count)
        return count <= limit, retry_after

    def healthcheck(self) -> bool:
        if self._redis is None:
            return settings.environment != "production"
        try:
            return bool(self._redis.ping())
        except RedisError:
            return False


limiter = RateLimiter()


def rate_limit(name: str, limit: int) -> Callable[..., None]:
    def dependency(
        request: Request,
        principal: Principal = Depends(get_current_principal),
    ) -> None:
        key = f"{name}:{principal.tenant_id}:{principal.subject}"
        allowed, retry_after = limiter.consume(key, limit)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded.",
                headers={"Retry-After": str(retry_after)},
            )
        request.state.rate_limit_name = name

    return dependency
