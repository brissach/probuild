import hashlib
import hmac
import time
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SignaturePayload:
  timestamp: str
  request_id: str
  body: bytes


def build_signature_message(payload: SignaturePayload) -> bytes:
  body_hash = hashlib.sha256(payload.body).hexdigest()
  message = f"{payload.timestamp}:{payload.request_id}:{body_hash}"
  return message.encode()


def sign_request(secret: str, payload: SignaturePayload) -> str:
  message = build_signature_message(payload)
  digest = hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()
  return digest


def verify_signature(
  secret: str,
  payload: SignaturePayload,
  provided_signature: str,
  *,
  max_age_seconds: int,
) -> tuple[bool, str | None]:
  try:
    timestamp = int(payload.timestamp)
  except ValueError:
    return False, "invalid timestamp"

  age = abs(int(time.time()) - timestamp)
  if age > max_age_seconds:
    return False, "expired timestamp"

  expected = sign_request(secret, payload)
  if not hmac.compare_digest(expected, provided_signature):
    return False, "invalid signature"

  return True, None
