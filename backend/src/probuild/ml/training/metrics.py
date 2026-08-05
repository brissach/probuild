from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TrainingMetrics:
  loss: float
  epoch: int
