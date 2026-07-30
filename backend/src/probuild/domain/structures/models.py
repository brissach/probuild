from dataclasses import dataclass

from probuild.domain.structures.bounds import StructureBounds
from probuild.domain.structures.coordinates import BlockCoordinate


@dataclass(frozen=True, slots=True)
class BlockPlacement:
  coordinate: BlockCoordinate
  block_id: str


@dataclass(frozen=True, slots=True)
class Structure:
  bounds: StructureBounds
  blocks: tuple[BlockPlacement, ...]

  @property
  def width(self) -> int:
    return self.bounds.width

  @property
  def height(self) -> int:
    return self.bounds.height

  @property
  def depth(self) -> int:
    return self.bounds.depth

  @property
  def block_count(self) -> int:
    return len(self.blocks)

  def non_air_blocks(self) -> tuple[BlockPlacement, ...]:
    return tuple(b for b in self.blocks if b.block_id != "air")
