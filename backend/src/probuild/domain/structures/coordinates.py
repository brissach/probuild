from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BlockCoordinate:
  x: int
  y: int
  z: int

  def in_bounds(self, width: int, height: int, depth: int) -> bool:
    return 0 <= self.x < width and 0 <= self.y < height and 0 <= self.z < depth
