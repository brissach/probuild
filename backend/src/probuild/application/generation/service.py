import time
import uuid
from dataclasses import dataclass

from probuild.application.validation.service import ValidationService
from probuild.common.errors import GenerationTimeoutError, ModelUnavailableError
from probuild.domain.generation.models import GenerationConfig, GenerationLimits
from probuild.domain.prompts.models import Prompt
from probuild.infrastructure.cache.redis import GenerationCache
from probuild.infrastructure.observability import metrics
from probuild.ml.inference.protocols import StructureGenerator
from probuild.ml.registry.model_registry import ModelRegistry
from probuild.ml.structures.serialization import structure_to_dict


@dataclass(frozen=True, slots=True)
class GenerationMetadata:
  seed: int
  duration_ms: int


@dataclass(frozen=True, slots=True)
class GenerationOutput:
  generation_id: str
  model_id: str
  model_version: str
  structure: dict[str, object]
  metadata: GenerationMetadata


class GenerationService:
  def __init__(
    self,
    *,
    generator: StructureGenerator | None,
    registry: ModelRegistry,
    validation: ValidationService,
    limits: GenerationLimits,
    cache: GenerationCache,
    default_model: str,
    timeout_seconds: float,
  ) -> None:
    self._generator = generator
    self._registry = registry
    self._validation = validation
    self._limits = limits
    self._cache = cache
    self._default_model = default_model
    self._timeout = timeout_seconds

  def _build_config(self, request: GenerationConfig) -> GenerationConfig:
    if not self._limits.accepts_dimensions(request.width, request.height, request.depth):
      raise ValueError("requested dimensions exceed limits")
    return GenerationConfig(
      seed=request.seed,
      width=request.width,
      height=request.height,
      depth=request.depth,
      temperature=request.temperature,
      top_k=request.top_k,
      top_p=request.top_p,
      max_tokens=min(request.max_tokens, self._limits.max_tokens),
    )

  def generate(
    self,
    *,
    prompt: str,
    config: GenerationConfig,
    model_ref: str | None = None,
  ) -> GenerationOutput:
    model_name = model_ref or self._default_model
    try:
      metadata = self._registry.resolve(model_name)
    except KeyError as exc:
      raise ModelUnavailableError(f"unknown model: {model_name}") from exc
    if self._generator is None or not self._registry.is_available(model_name):
      raise ModelUnavailableError(
        f"model {metadata.qualified_name} is not loaded; train and export a checkpoint first",
      )

    normalized_prompt = Prompt(text=prompt).normalized()
    resolved_config = self._build_config(config)

    cache_key = GenerationCache.cache_key(
      metadata.id,
      metadata.version,
      normalized_prompt,
      resolved_config,
    )
    cached = self._cache.get(cache_key)
    if cached:
      metrics.CACHE_HITS.inc()
      return GenerationOutput(
        generation_id=str(cached["generation_id"]),
        model_id=metadata.id,
        model_version=metadata.version,
        structure=cached["structure"],
        metadata=GenerationMetadata(
          seed=resolved_config.seed,
          duration_ms=int(cached["duration_ms"]),
        ),
      )

    metrics.CACHE_MISSES.inc()
    start = time.perf_counter()
    if time.perf_counter() - start > self._timeout:
      raise GenerationTimeoutError("Structure generation timed out.")

    structure = self._generator.generate(normalized_prompt, resolved_config)
    self._validation.validate_or_raise(structure)

    duration_ms = int((time.perf_counter() - start) * 1000)
    generation_id = str(uuid.uuid4())
    serialized = structure_to_dict(structure)

    self._cache.set(
      cache_key,
      {
        "generation_id": generation_id,
        "structure": serialized,
        "duration_ms": duration_ms,
      },
    )

    metrics.GENERATION_COUNT.labels(status="completed").inc()
    metrics.GENERATION_DURATION.observe(duration_ms / 1000.0)

    return GenerationOutput(
      generation_id=generation_id,
      model_id=metadata.id,
      model_version=metadata.version,
      structure=serialized,
      metadata=GenerationMetadata(
        seed=resolved_config.seed,
        duration_ms=duration_ms,
      ),
    )
