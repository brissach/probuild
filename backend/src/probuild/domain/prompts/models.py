from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Prompt:
  text: str

  def normalized(self) -> str:
    return " ".join(self.text.strip().split())
