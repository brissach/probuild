import numpy as np
import torch

from probuild.domain.structures.blocks import BlockRegistry
from probuild.domain.structures.bounds import StructureBounds


def one_hot_voxels(
  voxel_indices: np.ndarray,
  *,
  num_blocks: int,
) -> torch.Tensor:
  depth, height, width = voxel_indices.shape
  tensor = torch.zeros((num_blocks, width, height, depth), dtype=torch.float32)
  for x in range(width):
    for y in range(height):
      for z in range(depth):
        idx = int(voxel_indices[z, y, x])
        if 0 <= idx < num_blocks:
          tensor[idx, x, y, z] = 1.0
  return tensor.unsqueeze(0)


def structure_bounds_from_shape(shape: tuple[int, ...]) -> StructureBounds:
  if len(shape) != 3:
    raise ValueError("voxel shape must be depth x height x width")
  depth, height, width = shape
  return StructureBounds(width=width, height=height, depth=depth)


def indices_from_voxels(voxels: np.ndarray, registry: BlockRegistry) -> np.ndarray:
  return voxels.astype(np.int64)
