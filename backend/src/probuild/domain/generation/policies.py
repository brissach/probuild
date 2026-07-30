from probuild.domain.generation.models import GenerationLimits


def default_generation_limits(
  max_structure_size: int,
  max_generation_tokens: int,
  timeout_seconds: float,
) -> GenerationLimits:
  cube = int(max_structure_size ** (1 / 3))
  cube = max(8, min(cube, 64))
  return GenerationLimits(
    max_width=cube,
    max_height=cube,
    max_depth=cube,
    max_block_count=max_structure_size,
    max_tokens=max_generation_tokens,
    timeout_seconds=timeout_seconds,
  )
