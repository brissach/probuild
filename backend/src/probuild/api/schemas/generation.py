from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
  code: str
  message: str
  request_id: str | None = None


class ErrorResponse(BaseModel):
  error: ErrorDetail


class GenerationRequest(BaseModel):
  prompt: str = Field(min_length=1, max_length=512)
  seed: int = Field(default=0, ge=0, le=2_147_483_647)
  width: int = Field(default=32, ge=1, le=64)
  height: int = Field(default=32, ge=1, le=64)
  depth: int = Field(default=32, ge=1, le=64)
  temperature: float = Field(default=0.8, ge=0.0, le=2.0)
  top_k: int = Field(default=50, ge=0, le=512)
  top_p: float = Field(default=1.0, ge=0.0, le=1.0)
  model: str | None = None


class ModelInfo(BaseModel):
  id: str
  version: str
  architecture: str
  loaded: bool


class GenerationMetadataResponse(BaseModel):
  seed: int
  duration_ms: int


class StructureResponse(BaseModel):
  width: int
  height: int
  depth: int
  blocks: list[dict[str, int | str]]


class GenerationResponse(BaseModel):
  generation_id: str
  model: ModelInfo
  structure: StructureResponse
  metadata: GenerationMetadataResponse
