import uuid
from collections.abc import Callable

import redis
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from probuild.infrastructure.config.settings import Settings


class RequestIdMiddleware(BaseHTTPMiddleware):
  async def dispatch(self, request: Request, call_next: Callable) -> Response:
    request_id = request.headers.get("X-ProBuild-Request-Id") or str(uuid.uuid4())
    request.state.request_id = request_id
    if request.method in {"POST", "PUT", "PATCH"}:
      request.state.body = await request.body()
    response = await call_next(request)
    response.headers["X-ProBuild-Request-Id"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response


class PayloadLimitMiddleware(BaseHTTPMiddleware):
  def __init__(self, app: FastAPI, *, max_bytes: int) -> None:
    super().__init__(app)
    self._max_bytes = max_bytes

  async def dispatch(self, request: Request, call_next: Callable) -> Response:
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > self._max_bytes:
      return Response(status_code=413, content="payload too large")
    return await call_next(request)


def create_redis_client(settings: Settings) -> redis.Redis | None:
  if not settings.redis_enabled:
    return None
  return redis.Redis.from_url(settings.redis_url, decode_responses=True)
