from pathlib import Path

import torch


class CheckpointManager:
  def __init__(self, directory: Path) -> None:
    self._directory = directory
    self._directory.mkdir(parents=True, exist_ok=True)

  def save(
    self,
    model: torch.nn.Module,
    *,
    name: str,
    metadata: dict[str, object] | None = None,
  ) -> Path:
    path = self._directory / name
    payload: dict[str, object] = {"state_dict": model.state_dict()}
    if metadata:
      payload["metadata"] = metadata
    torch.save(payload, path)
    return path

  def latest(self) -> Path | None:
    checkpoints = sorted(self._directory.glob("*.pt"))
    return checkpoints[-1] if checkpoints else None
