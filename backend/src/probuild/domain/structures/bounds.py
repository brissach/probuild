from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StructureBounds:
  width: int
  height: int
  depth: int

  @property
  def volume(self) -> int:
    return self.width * self.height * self.depth

  @property
  def block_capacity(self) -> int:
    return self.volume
