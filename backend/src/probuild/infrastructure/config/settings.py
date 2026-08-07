from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
  model_config = SettingsConfigDict(
    env_prefix="PROBUILD_",
    env_file=".env",
    env_file_encoding="utf-8",
    extra="ignore",
  )

  env: str = "development"
  api_host: str = "0.0.0.0"
  api_port: int = 8000
  api_key: str = Field(default="dev-api-key-change-in-production", min_length=8)
  signing_secret: str = Field(default="dev-signing-secret-change-in-production", min_length=16)
  model_path: str | None = None
  model_version: str = "0.1.0"
  device: str = "cpu"
  redis_url: str | None = None
  max_structure_size: int = Field(default=32768, ge=1024)
  max_generation_tokens: int = Field(default=512, ge=64, le=4096)
  generation_timeout: float = Field(default=120.0, ge=5.0)
  log_level: str = "INFO"
  cors_origins: str = ""
  rate_limit_per_minute: int = Field(default=60, ge=1)
  signature_max_age_seconds: int = Field(default=300, ge=30)
  cache_ttl_seconds: int = Field(default=3600, ge=60)
  max_request_body_bytes: int = Field(default=65536, ge=1024)

  @property
  def cors_origin_list(self) -> list[str]:
    if not self.cors_origins.strip():
      return []
    return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

  @property
  def redis_enabled(self) -> bool:
    return bool(self.redis_url)


def load_settings() -> Settings:
  return Settings()
