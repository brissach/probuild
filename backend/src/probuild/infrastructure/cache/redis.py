import json
from typing import Any

from probuild.common.utilities import stable_hash
from probuild.domain.generation.models import GenerationConfig


class GenerationCache:
  def __init__(self, client: Any | None, *, ttl_seconds: int) -> None:
    self._client = client
    self._ttl_seconds = ttl_seconds

  @staticmethod
  def cache_key(
    model_id: str,
    model_version: str,
    prompt: str,
    config: GenerationConfig,
  ) -> str:
    payload = {
      "model_id": model_id,
      "model_version": model_version,
      "prompt": prompt,
      "seed": config.seed,
      "width": config.width,
      "height": config.height,
      "depth": config.depth,
      "temperature": config.temperature,
      "top_k": config.top_k,
      "top_p": config.top_p,
      "max_tokens": config.max_tokens,
    }
    return f"probuild:gen:{stable_hash(payload)}"

  def get(self, key: str) -> dict[str, Any] | None:
    if self._client is None:
      return None
    raw = self._client.get(key)
    if raw is None:
      return None
    return json.loads(raw)

  def set(self, key: str, value: dict[str, Any]) -> None:
    if self._client is None:
      return
    self._client.setex(key, self._ttl_seconds, json.dumps(value))
