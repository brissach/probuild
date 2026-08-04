from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class ModelMetadata:
  id: str
  version: str
  architecture: str
  checkpoint: str | None
  created_at: datetime
  metadata: dict[str, Any] = field(default_factory=dict)

  @property
  def qualified_name(self) -> str:
    return f"{self.id}@{self.version}"

  @property
  def is_loaded(self) -> bool:
    return self.checkpoint is not None
