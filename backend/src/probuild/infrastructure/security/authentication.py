import hmac
import secrets


def constant_time_compare(left: str, right: str) -> bool:
  return hmac.compare_digest(left.encode(), right.encode())


def verify_api_key(provided: str | None, expected: str) -> bool:
  if not provided:
    return False
  return constant_time_compare(provided, expected)


def generate_request_id() -> str:
  return secrets.token_hex(16)
