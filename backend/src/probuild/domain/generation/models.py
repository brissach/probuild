from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GenerationConfig:
  seed: int
  width: int
  height: int
  depth: int
  temperature: float
  top_k: int
  top_p: float
  max_tokens: int


@dataclass(frozen=True, slots=True)
class GenerationLimits:
  max_width: int
  max_height: int
  max_depth: int
  max_block_count: int
  max_tokens: int
  timeout_seconds: float

  def accepts_dimensions(self, width: int, height: int, depth: int) -> bool:
    return (
      1 <= width <= self.max_width
      and 1 <= height <= self.max_height
      and 1 <= depth <= self.max_depth
    )
