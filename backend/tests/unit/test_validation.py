from probuild.application.validation.service import ValidationService
from probuild.domain.generation.models import GenerationLimits
from probuild.domain.structures.blocks import default_block_registry
from probuild.domain.structures.bounds import StructureBounds
from probuild.domain.structures.coordinates import BlockCoordinate
from probuild.domain.structures.models import BlockPlacement, Structure


def make_limits() -> GenerationLimits:
  return GenerationLimits(
    max_width=32,
    max_height=32,
    max_depth=32,
    max_block_count=1000,
    max_tokens=128,
    timeout_seconds=30.0,
  )


def test_validation_rejects_unknown_block() -> None:
  service = ValidationService(registry=default_block_registry(), limits=make_limits())
  structure = Structure(
    bounds=StructureBounds(width=4, height=4, depth=4),
    blocks=(
      BlockPlacement(
        coordinate=BlockCoordinate(x=0, y=0, z=0),
        block_id="netherite_block",
      ),
    ),
  )
  result = service.validate(structure)
  assert not result.valid


def test_validation_rejects_out_of_bounds() -> None:
  service = ValidationService(registry=default_block_registry(), limits=make_limits())
  structure = Structure(
    bounds=StructureBounds(width=4, height=4, depth=4),
    blocks=(
      BlockPlacement(
        coordinate=BlockCoordinate(x=5, y=0, z=0),
        block_id="stone",
      ),
    ),
  )
  result = service.validate(structure)
  assert not result.valid
