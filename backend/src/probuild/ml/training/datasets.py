from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import numpy as np


@dataclass(frozen=True, slots=True)
class StructureSample:
  prompt: str
  voxels: np.ndarray
  metadata: dict[str, Any]


class StructureDataset(Protocol):
  def __len__(self) -> int:
    ...

  def __getitem__(self, index: int) -> StructureSample:
    ...


class NumpyStructureDataset:
  def __init__(self, samples: tuple[StructureSample, ...]) -> None:
    self._samples = samples

  def __len__(self) -> int:
    return len(self._samples)

  def __getitem__(self, index: int) -> StructureSample:
    return self._samples[index]


def load_npz_dataset(path: Path) -> NumpyStructureDataset:
  with np.load(path, allow_pickle=True) as data:
    prompts = data["prompts"].tolist()
    voxels = data["voxels"]
    metadata = data["metadata"].tolist() if "metadata" in data else [{} for _ in prompts]
  samples = tuple(
    StructureSample(prompt=str(prompts[i]), voxels=voxels[i], metadata=metadata[i])
    for i in range(len(prompts))
  )
  return NumpyStructureDataset(samples)


def load_npy_dataset(path: Path) -> NumpyStructureDataset:
  array = np.load(path, allow_pickle=True)
  samples = tuple(
    StructureSample(
      prompt=str(item["prompt"]),
      voxels=item["voxels"],
      metadata=dict(item.get("metadata", {})),
    )
    for item in array
  )
  return NumpyStructureDataset(samples)
