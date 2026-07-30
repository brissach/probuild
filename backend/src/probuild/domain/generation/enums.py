from enum import StrEnum


class GenerationStatus(StrEnum):
  PENDING = "pending"
  RUNNING = "running"
  COMPLETED = "completed"
  FAILED = "failed"


class ModelArchitecture(StrEnum):
  PROBUILD_BASE = "probuild-base"
  VOXEL_AE_TRANSFORMER = "voxel_ae_transformer"


class SamplingStrategy(StrEnum):
  GREEDY = "greedy"
  TEMPERATURE = "temperature"
  TOP_K = "top_k"
  TOP_P = "top_p"
