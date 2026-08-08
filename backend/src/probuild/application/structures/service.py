from probuild.domain.structures.models import Structure
from probuild.ml.structures.serialization import structure_from_dict, structure_to_dict


class StructureService:
  def serialize(self, structure: Structure) -> dict[str, object]:
    return structure_to_dict(structure)

  def deserialize(self, payload: dict[str, object]) -> Structure:
    return structure_from_dict(payload)
