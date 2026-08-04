from dataclasses import dataclass
from pathlib import Path

import torch

from probuild.common.errors import ModelUnavailableError
from probuild.infrastructure.observability.metrics import MODEL_LOAD_TIME
from probuild.ml.registry.model_metadata import ModelMetadata


@dataclass(frozen=True, slots=True)
class ModelRecord:
  metadata: ModelMetadata
  state_dict: dict[str, torch.Tensor] | None


class ModelRegistry:
  def __init__(self) -> None:
    self._models: dict[str, ModelMetadata] = {}
    self._aliases: dict[str, str] = {}
    self._loaded: dict[str, dict[str, torch.Tensor]] = {}

  def register(self, metadata: ModelMetadata, *, aliases: tuple[str, ...] = ()) -> None:
    self._models[metadata.qualified_name] = metadata
    for alias in aliases:
      self._aliases[alias] = metadata.qualified_name

  def resolve(self, model_ref: str) -> ModelMetadata:
    qualified = self._aliases.get(model_ref, model_ref)
    if qualified not in self._models:
      raise KeyError(f"unknown model: {model_ref}")
    return self._models[qualified]

  def list_models(self) -> tuple[ModelMetadata, ...]:
    return tuple(self._models.values())

  def load_checkpoint(self, model_ref: str, checkpoint_path: Path, device: str) -> ModelRecord:
    metadata = self.resolve(model_ref)
    if not checkpoint_path.exists():
      return ModelRecord(metadata=metadata, state_dict=None)

    with MODEL_LOAD_TIME.time():
      payload = torch.load(checkpoint_path, map_location=device, weights_only=True)
    state_dict = (
      payload["state_dict"]
      if isinstance(payload, dict) and "state_dict" in payload
      else payload
    )
    if not isinstance(state_dict, dict):
      raise ModelUnavailableError("checkpoint format is invalid")

    loaded_metadata = ModelMetadata(
      id=metadata.id,
      version=metadata.version,
      architecture=metadata.architecture,
      checkpoint=str(checkpoint_path),
      created_at=metadata.created_at,
      metadata=metadata.metadata,
    )
    self._models[metadata.qualified_name] = loaded_metadata
    self._loaded[metadata.qualified_name] = state_dict
    return ModelRecord(metadata=loaded_metadata, state_dict=state_dict)

  def get_state_dict(self, model_ref: str) -> dict[str, torch.Tensor]:
    metadata = self.resolve(model_ref)
    state = self._loaded.get(metadata.qualified_name)
    if state is None:
      raise ModelUnavailableError(
        f"model {metadata.qualified_name} has no loaded checkpoint",
      )
    return state

  def is_available(self, model_ref: str) -> bool:
    try:
      metadata = self.resolve(model_ref)
    except KeyError:
      return False
    return metadata.checkpoint is not None and metadata.qualified_name in self._loaded
