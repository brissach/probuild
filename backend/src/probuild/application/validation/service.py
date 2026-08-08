from dataclasses import dataclass

from probuild.common.errors import StructureValidationError
from probuild.domain.generation.models import GenerationLimits
from probuild.domain.structures.blocks import BlockRegistry
from probuild.domain.structures.models import Structure


@dataclass(frozen=True, slots=True)
class ValidationIssue:
  code: str
  message: str


@dataclass(frozen=True, slots=True)
class ValidationResult:
  valid: bool
  issues: tuple[ValidationIssue, ...] = ()

  @staticmethod
  def ok() -> "ValidationResult":
    return ValidationResult(valid=True)

  @staticmethod
  def failed(*issues: ValidationIssue) -> "ValidationResult":
    return ValidationResult(valid=False, issues=issues)


def validate_schema(structure: Structure) -> ValidationResult:
  if structure.width < 1 or structure.height < 1 or structure.depth < 1:
    return ValidationResult.failed(
      ValidationIssue("INVALID_DIMENSIONS", "structure dimensions must be positive"),
    )
  return ValidationResult.ok()


def validate_bounds(structure: Structure, limits: GenerationLimits) -> ValidationResult:
  if not limits.accepts_dimensions(structure.width, structure.height, structure.depth):
    return ValidationResult.failed(
      ValidationIssue("DIMENSIONS_EXCEEDED", "structure dimensions exceed configured limits"),
    )
  if structure.block_count > limits.max_block_count:
    return ValidationResult.failed(
      ValidationIssue("BLOCK_COUNT_EXCEEDED", "structure block count exceeds limit"),
    )
  return ValidationResult.ok()


def validate_materials(structure: Structure, registry: BlockRegistry) -> ValidationResult:
  invalid = [
    block.block_id
    for block in structure.blocks
    if not registry.is_supported(block.block_id)
  ]
  if invalid:
    return ValidationResult.failed(
      ValidationIssue("UNSUPPORTED_MATERIAL", f"unsupported blocks: {sorted(set(invalid))}"),
    )
  return ValidationResult.ok()


def validate_coordinates(structure: Structure) -> ValidationResult:
  for block in structure.blocks:
    if not block.coordinate.in_bounds(structure.width, structure.height, structure.depth):
      return ValidationResult.failed(
        ValidationIssue(
          "OUT_OF_BOUNDS",
          f"block at ({block.coordinate.x}, {block.coordinate.y}, {block.coordinate.z}) "
          f"is outside structure bounds",
        ),
      )
  return ValidationResult.ok()


def validate_connectivity(structure: Structure) -> ValidationResult:
  solids = {
    (b.coordinate.x, b.coordinate.y, b.coordinate.z)
    for b in structure.non_air_blocks()
  }
  if len(solids) <= 1:
    return ValidationResult.ok()

  start = next(iter(solids))
  visited = {start}
  stack = [start]
  neighbors = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]

  while stack:
    current = stack.pop()
    x, y, z = current
    for dx, dy, dz in neighbors:
      nxt = (x + dx, y + dy, z + dz)
      if nxt in solids and nxt not in visited:
        visited.add(nxt)
        stack.append(nxt)

  if visited != solids:
    return ValidationResult.failed(
      ValidationIssue("DISCONNECTED", "structure contains disconnected solid components"),
    )
  return ValidationResult.ok()


class ValidationService:
  def __init__(
    self,
    *,
    registry: BlockRegistry,
    limits: GenerationLimits,
    check_connectivity: bool = False,
  ) -> None:
    self._registry = registry
    self._limits = limits
    self._check_connectivity = check_connectivity

  def validate(self, structure: Structure) -> ValidationResult:
    checks = (
      validate_schema(structure),
      validate_bounds(structure, self._limits),
      validate_materials(structure, self._registry),
      validate_coordinates(structure),
    )
    issues = [issue for result in checks for issue in result.issues]
    if issues:
      return ValidationResult.failed(*issues)

    if self._check_connectivity:
      connectivity = validate_connectivity(structure)
      if not connectivity.valid:
        return connectivity

    return ValidationResult.ok()

  def validate_or_raise(self, structure: Structure) -> None:
    result = self.validate(structure)
    if not result.valid:
      message = "; ".join(issue.message for issue in result.issues)
      raise StructureValidationError(message)
