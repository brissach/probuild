from typing import Protocol

from probuild.domain.generation.models import GenerationConfig
from probuild.domain.structures.models import Structure


class StructureGenerator(Protocol):
  def generate(self, prompt: str, config: GenerationConfig) -> Structure:
    ...
