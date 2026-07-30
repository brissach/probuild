class ProbuildError(Exception):
  code: str = "INTERNAL_ERROR"

  def __init__(self, message: str, *, request_id: str | None = None) -> None:
    super().__init__(message)
    self.message = message
    self.request_id = request_id


class ValidationError(ProbuildError):
  code = "VALIDATION_ERROR"


class AuthenticationError(ProbuildError):
  code = "AUTHENTICATION_FAILED"


class SignatureError(ProbuildError):
  code = "INVALID_SIGNATURE"


class ReplayError(ProbuildError):
  code = "REPLAY_DETECTED"


class RateLimitError(ProbuildError):
  code = "RATE_LIMIT_EXCEEDED"


class GenerationError(ProbuildError):
  code = "GENERATION_FAILED"


class GenerationTimeoutError(GenerationError):
  code = "GENERATION_TIMEOUT"


class ModelUnavailableError(ProbuildError):
  code = "MODEL_UNAVAILABLE"


class StructureValidationError(ProbuildError):
  code = "STRUCTURE_VALIDATION_FAILED"
