from pathlib import Path


class ArtifactStore:
  def __init__(self, root: Path) -> None:
    self._root = root

  @property
  def root(self) -> Path:
    return self._root

  def resolve(self, relative: str) -> Path:
    path = (self._root / relative).resolve()
    if not str(path).startswith(str(self._root.resolve())):
      raise ValueError("artifact path escapes root")
    return path

  def ensure(self) -> None:
    self._root.mkdir(parents=True, exist_ok=True)
