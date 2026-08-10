import json

from fastapi import APIRouter, Depends, HTTPException, Request

from probuild.api.dependencies import AppContainer
from probuild.api.schemas.generation import (
  GenerationMetadataResponse,
  GenerationRequest,
  GenerationResponse,
  ModelInfo,
  StructureResponse,
)
from probuild.common.errors import (
  GenerationTimeoutError,
  ModelUnavailableError,
  ProbuildError,
  StructureValidationError,
  ValidationError,
)
from probuild.domain.generation.models import GenerationConfig
from probuild.infrastructure.security.authentication import verify_api_key
from probuild.infrastructure.security.signing import SignaturePayload, verify_signature

router = APIRouter(prefix="/v1")


def get_container(request: Request) -> AppContainer:
  return request.app.state.container


async def verify_signed_request(request: Request) -> GenerationRequest:
  container = get_container(request)
  settings = container.settings

  auth_header = request.headers.get("Authorization", "")
  if not auth_header.startswith("Bearer "):
    raise HTTPException(status_code=401, detail="missing bearer token")
  token = auth_header.removeprefix("Bearer ").strip()
  if not verify_api_key(token, settings.api_key):
    raise HTTPException(status_code=401, detail="invalid api key")

  timestamp = request.headers.get("X-ProBuild-Timestamp")
  request_id = request.headers.get("X-ProBuild-Request-Id")
  signature = request.headers.get("X-ProBuild-Signature")
  if not timestamp or not request_id or not signature:
    raise HTTPException(status_code=401, detail="missing signature headers")

  if not container.replay_guard.check_and_record(request_id):
    raise HTTPException(status_code=409, detail="duplicate request id")

  body = getattr(request.state, "body", b"")
  valid, reason = verify_signature(
    settings.signing_secret,
    SignaturePayload(timestamp=timestamp, request_id=request_id, body=body),
    signature,
    max_age_seconds=settings.signature_max_age_seconds,
  )
  if not valid:
    raise HTTPException(status_code=401, detail=reason or "invalid signature")

  client_key = request.client.host if request.client else "unknown"
  if not container.rate_limiter.allow(client_key):
    raise HTTPException(status_code=429, detail="rate limit exceeded")

  try:
    return GenerationRequest.model_validate(json.loads(body))
  except json.JSONDecodeError as exc:
    raise HTTPException(status_code=400, detail="invalid json body") from exc


@router.post("/generation", response_model=GenerationResponse)
async def create_generation(
  payload: GenerationRequest = Depends(verify_signed_request),
  container: AppContainer = Depends(get_container),
) -> GenerationResponse:
  config = GenerationConfig(
    seed=payload.seed,
    width=payload.width,
    height=payload.height,
    depth=payload.depth,
    temperature=payload.temperature,
    top_k=payload.top_k,
    top_p=payload.top_p,
    max_tokens=container.settings.max_generation_tokens,
  )
  try:
    result = container.generation_service.generate(
      prompt=payload.prompt,
      config=config,
      model_ref=payload.model,
    )
  except ModelUnavailableError as exc:
    raise HTTPException(status_code=503, detail=exc.message) from exc
  except GenerationTimeoutError as exc:
    raise HTTPException(status_code=504, detail=exc.message) from exc
  except StructureValidationError as exc:
    raise HTTPException(status_code=422, detail=exc.message) from exc
  except ValidationError as exc:
    raise HTTPException(status_code=400, detail=exc.message) from exc
  except ValueError as exc:
    raise HTTPException(status_code=400, detail=str(exc)) from exc
  except ProbuildError as exc:
    raise HTTPException(status_code=500, detail=exc.message) from exc

  return GenerationResponse(
    generation_id=result.generation_id,
    model=ModelInfo(
      id=result.model_id,
      version=result.model_version,
      architecture="probuild-base",
      loaded=True,
    ),
    structure=StructureResponse(**result.structure),
    metadata=GenerationMetadataResponse(
      seed=result.metadata.seed,
      duration_ms=result.metadata.duration_ms,
    ),
  )
