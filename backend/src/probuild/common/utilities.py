import hashlib
import json
from typing import Any


def stable_hash(payload: dict[str, Any]) -> str:
  encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
  return hashlib.sha256(encoded).hexdigest()


def clamp(value: float, lower: float, upper: float) -> float:
  return max(lower, min(upper, value))
