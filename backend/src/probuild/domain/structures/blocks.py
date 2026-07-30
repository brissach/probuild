from dataclasses import dataclass

DEFAULT_BLOCKS: tuple[str, ...] = (
  "air",
  "stone",
  "cobblestone",
  "stone_bricks",
  "oak_planks",
  "oak_log",
  "oak_leaves",
  "glass",
  "bricks",
  "dirt",
  "grass_block",
  "sand",
  "spruce_planks",
  "spruce_log",
  "water",
  "torch",
)


@dataclass(frozen=True, slots=True)
class BlockRegistry:
  blocks: tuple[str, ...]

  def __post_init__(self) -> None:
    if "air" not in self.blocks:
      raise ValueError("block registry must include air")
    if len(set(self.blocks)) != len(self.blocks):
      raise ValueError("block registry contains duplicates")

  @property
  def size(self) -> int:
    return len(self.blocks)

  def index_of(self, block_id: str) -> int:
    try:
      return self.blocks.index(block_id)
    except ValueError as exc:
      raise KeyError(f"unknown block: {block_id}") from exc

  def id_at(self, index: int) -> str:
    if index < 0 or index >= len(self.blocks):
      raise IndexError(f"block index out of range: {index}")
    return self.blocks[index]

  def is_supported(self, block_id: str) -> bool:
    return block_id in self.blocks


def default_block_registry() -> BlockRegistry:
  return BlockRegistry(blocks=DEFAULT_BLOCKS)
