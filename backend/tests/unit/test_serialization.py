from probuild.domain.structures.bounds import StructureBounds
from probuild.domain.structures.coordinates import BlockCoordinate
from probuild.domain.structures.models import BlockPlacement, Structure
from probuild.ml.structures.serialization import structure_from_dict, structure_to_dict


def test_structure_roundtrip() -> None:
  structure = Structure(
    bounds=StructureBounds(width=2, height=2, depth=2),
    blocks=(
      BlockPlacement(
        coordinate=BlockCoordinate(x=0, y=0, z=0),
        block_id="stone",
      ),
    ),
  )
  payload = structure_to_dict(structure)
  restored = structure_from_dict(payload)
  assert restored.width == 2
  assert restored.blocks[0].block_id == "stone"
