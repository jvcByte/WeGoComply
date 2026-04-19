from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from threading import Lock

from fastapi.responses import JSONResponse
from schemas.common import ErrorBody, ErrorResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    limit: int
    remaining: int
    reset_at: int


class InMemoryRateLimiter:
    def __init__(self, limit: int, window_seconds: int) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._lock = Lock()
        self._store: dict[str, tuple[int, int]] = {}

    def hit(self, key: str) -> RateLimitResult:
        with self._lock:
            window_start = self._current_window_start()
            expires_at = window_start + self.window_seconds
            count, stored_window_start = self._store.get(key, (0, window_start))
            if stored_window_start != window_start:
                count = 0
            count += 1
            self._store[key] = (count, window_start)

        return RateLimitResult(
            allowed=count <= self.limit,
            limit=self.limit,
            remaining=max(self.limit - count, 0),
            reset_at=expires_at,
        )

    def validate_connection(self) -> None:
        return None

    def _current_window_start(self) -> int:
        now = int(time.time())
        return now - (now % self.window_seconds)


class RedisRateLimiter:
    def __init__(self, redis_url: str, limit: int, window_seconds: int) -> None:
        import redis

        self.limit = limit
        self.window_seconds = window_seconds
        self._client = redis.Redis.from_url(redis_url, decode_responses=True)

    def hit(self, key: str) -> RateLimitResult:
        window_start = self._current_window_start()
        expires_at = window_start + self.window_seconds
        window_key = f"ratelimit:{key}:{window_start}"
        count = int(self._client.incr(window_key))
        if count == 1:
            self._client.expire(window_key, self.window_seconds + 1)

        return RateLimitResult(
            allowed=count <= self.limit,
            limit=self.limit,
            remaining=max(self.limit - count, 0),
            reset_at=expires_at,
        )

    def validate_connection(self) -> None:
        self._client.ping()

    def _current_window_start(self) -> int:
        now = int(time.time())
        return now - (now % self.window_seconds)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, rate_limiter, enabled: bool = True) -> None:
        super().__init__(app)
        self.rate_limiter = rate_limiter
        self.enabled = enabled

    async def dispatch(self, request: Request, call_next) -> Response:
        if not self.enabled or request.method == "OPTIONS" or not request.url.path.startswith("/api"):
            return await call_next(request)

        key = self._build_key(request)
        result = self.rate_limiter.hit(key)
        if not result.allowed:
            response = JSONResponse(
                status_code=429,
                content=ErrorResponse(
                    error=ErrorBody(
                        code="RATE_LIMIT_EXCEEDED",
                        message="Rate limit exceeded. Try again later.",
                        details={"limit": result.limit, "reset_at": result.reset_at},
                    )
                ).model_dump(),
            )
        else:
            response = await call_next(request)

        response.headers["X-RateLimit-Limit"] = str(result.limit)
        response.headers["X-RateLimit-Remaining"] = str(result.remaining)
        response.headers["X-RateLimit-Reset"] = str(result.reset_at)
        if not result.allowed:
            retry_after = max(result.reset_at - int(time.time()), 0)
            response.headers["Retry-After"] = str(retry_after)
        return response

    @staticmethod
    def _build_key(request: Request) -> str:
        mock_user = request.headers.get("X-Mock-User")
        if mock_user:
            subject = f"user:{mock_user}"
        elif request.headers.get("Authorization"):
            digest = hashlib.sha256(request.headers["Authorization"].encode("utf-8")).hexdigest()[:16]
            subject = f"token:{digest}"
        elif request.client:
            subject = f"ip:{request.client.host}"
        else:
            subject = "anonymous"
        return f"{subject}:{request.method}:{request.url.path}"
