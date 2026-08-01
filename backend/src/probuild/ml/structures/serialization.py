import json
from typing import Any

from probuild.domain.structures.models import BlockPlacement, Structure


def structure_to_dict(structure: Structure) -> dict[str, Any]:
  return {
    "width": structure.width,
    "height": structure.height,
    "depth": structure.depth,
    "blocks": [
      {
        "x": block.coordinate.x,
        "y": block.coordinate.y,
        "z": block.coordinate.z,
        "id": block.block_id,
      }
      for block in structure.blocks
    ],
  }


def structure_from_dict(payload: dict[str, Any]) -> Structure:
  from probuild.domain.structures.bounds import StructureBounds
  from probuild.domain.structures.coordinates import BlockCoordinate

  bounds = StructureBounds(
    width=int(payload["width"]),
    height=int(payload["height"]),
    depth=int(payload["depth"]),
  )
  blocks = tuple(
    BlockPlacement(
      coordinate=BlockCoordinate(
        x=int(entry["x"]),
        y=int(entry["y"]),
        z=int(entry["z"]),
      ),
      block_id=str(entry["id"]),
    )
    for entry in payload.get("blocks", [])
  )
  return Structure(bounds=bounds, blocks=blocks)


def structure_to_json(structure: Structure) -> str:
  return json.dumps(structure_to_dict(structure), separators=(",", ":"))


def structure_from_json(raw: str) -> Structure:
  return structure_from_dict(json.loads(raw))
