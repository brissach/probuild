import time

from probuild.infrastructure.security.replay import ReplayGuard
from probuild.infrastructure.security.signing import (
  SignaturePayload,
  sign_request,
  verify_signature,
)


def test_signature_roundtrip() -> None:
  body = b'{"prompt":"tower"}'
  payload = SignaturePayload(timestamp=str(int(time.time())), request_id="abc", body=body)
  signature = sign_request("secret-value-1234567890", payload)
  valid, reason = verify_signature(
    "secret-value-1234567890",
    payload,
    signature,
    max_age_seconds=300,
  )
  assert valid
  assert reason is None


def test_replay_guard() -> None:
  guard = ReplayGuard()
  assert guard.check_and_record("req-1")
  assert not guard.check_and_record("req-1")
