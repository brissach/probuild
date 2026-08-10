from dataclasses import dataclass

from probuild.application.generation.service import GenerationService
from probuild.application.validation.service import ValidationService
from probuild.infrastructure.cache.redis import GenerationCache
from probuild.infrastructure.config.settings import Settings
from probuild.infrastructure.security.rate_limit import RateLimiter
from probuild.infrastructure.security.replay import ReplayGuard
from probuild.ml.registry.model_registry import ModelRegistry


@dataclass(frozen=True, slots=True)
class AppContainer:
  settings: Settings
  generation_service: GenerationService
  validation_service: ValidationService
  model_registry: ModelRegistry
  replay_guard: ReplayGuard
  rate_limiter: RateLimiter
  cache: GenerationCache
