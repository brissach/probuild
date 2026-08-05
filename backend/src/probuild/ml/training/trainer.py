from dataclasses import dataclass
from pathlib import Path

import torch
from torch.utils.data import DataLoader, TensorDataset

from probuild.ml.training.datasets import StructureDataset, StructureSample


@dataclass(frozen=True, slots=True)
class TrainingConfig:
  epochs: int = 10
  batch_size: int = 4
  learning_rate: float = 1e-4
  checkpoint_dir: Path = Path("artifacts/checkpoints")
  device: str = "cpu"


class Trainer:
  def __init__(
    self,
    *,
    model: torch.nn.Module,
    config: TrainingConfig,
    dataset: StructureDataset,
  ) -> None:
    self._model = model
    self._config = config
    self._dataset = dataset
    self._optimizer = torch.optim.AdamW(model.parameters(), lr=config.learning_rate)

  def _collate(self, batch: list[StructureSample]) -> torch.Tensor:
    tensors = [torch.tensor(sample.voxels, dtype=torch.float32) for sample in batch]
    return torch.stack(tensors)

  def train_epoch(self) -> float:
    tensors = torch.stack([
      torch.tensor(self._dataset[index].voxels, dtype=torch.float32)
      for index in range(len(self._dataset))
    ])
    loader: DataLoader[torch.Tensor] = DataLoader(
      TensorDataset(tensors),
      batch_size=self._config.batch_size,
      shuffle=True,
    )
    self._model.train()
    total_loss = 0.0
    steps = 0
    for batch in loader:
      inputs = batch[0].to(self._config.device)
      self._optimizer.zero_grad()
      outputs = self._model(inputs)
      if isinstance(outputs, tuple):
        reconstruction, _ = outputs[:2]
        loss = torch.nn.functional.mse_loss(reconstruction, inputs)
      else:
        loss = torch.nn.functional.mse_loss(outputs, inputs)
      loss.backward()
      self._optimizer.step()
      total_loss += float(loss.item())
      steps += 1
    return total_loss / max(steps, 1)

  def run(self) -> None:
    self._config.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    for epoch in range(self._config.epochs):
      loss = self.train_epoch()
      checkpoint = self._config.checkpoint_dir / f"epoch_{epoch + 1}.pt"
      torch.save(
        {"state_dict": self._model.state_dict(), "epoch": epoch + 1, "loss": loss},
        checkpoint,
      )
