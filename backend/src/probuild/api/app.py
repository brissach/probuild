from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app
from starlette.middleware.cors import CORSMiddleware

from probuild import __version__
from probuild.api.dependencies import AppContainer
from probuild.api.middleware import PayloadLimitMiddleware, RequestIdMiddleware, create_redis_client
from probuild.api.routes import generation, health, models
from probuild.api.schemas.generation import ErrorDetail, ErrorResponse
from probuild.application.generation.service import GenerationService
from probuild.application.validation.service import ValidationService
from probuild.domain.generation.policies import default_generation_limits
from probuild.domain.structures.blocks import default_block_registry
from probuild.infrastructure.cache.redis import GenerationCache
from probuild.infrastructure.config.settings import load_settings
from probuild.infrastructure.observability.logging import configure_logging
from probuild.infrastructure.security.rate_limit import RateLimiter
from probuild.infrastructure.security.replay import ReplayGuard
from probuild.ml.bootstrap import build_generator, build_model_registry


def create_app() -> FastAPI:
  settings = load_settings()
  configure_logging(settings.log_level)

  registry = build_model_registry(settings)
  generator = build_generator(settings, registry)
  limits = default_generation_limits(
    settings.max_structure_size,
    settings.max_generation_tokens,
    settings.generation_timeout,
  )
  validation = ValidationService(registry=default_block_registry(), limits=limits)
  cache = GenerationCache(create_redis_client(settings), ttl_seconds=settings.cache_ttl_seconds)
  generation_service = GenerationService(
    generator=generator,
    registry=registry,
    validation=validation,
    limits=limits,
    cache=cache,
    default_model="probuild-base",
    timeout_seconds=settings.generation_timeout,
  )

  container = AppContainer(
    settings=settings,
    generation_service=generation_service,
    validation_service=validation,
    model_registry=registry,
    replay_guard=ReplayGuard(ttl_seconds=settings.signature_max_age_seconds * 2),
    rate_limiter=RateLimiter(limit_per_minute=settings.rate_limit_per_minute),
    cache=cache,
  )

  app = FastAPI(title="Probuild API", version=__version__)
  app.state.container = container

  if settings.cors_origin_list:
    app.add_middleware(
      CORSMiddleware,
      allow_origins=settings.cors_origin_list,
      allow_methods=["GET", "POST"],
      allow_headers=["*"],
    )

  app.add_middleware(PayloadLimitMiddleware, max_bytes=settings.max_request_body_bytes)
  app.add_middleware(RequestIdMiddleware)

  app.include_router(health.router, tags=["health"])
  app.include_router(models.router, tags=["models"])
  app.include_router(generation.router, tags=["generation"])
  app.mount("/metrics", make_asgi_app())

  @app.exception_handler(RequestValidationError)
  async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
      status_code=422,
      content=ErrorResponse(
        error=ErrorDetail(
          code="VALIDATION_ERROR",
          message=str(exc.errors()),
          request_id=request_id,
        ),
      ).model_dump(),
    )

  return app
