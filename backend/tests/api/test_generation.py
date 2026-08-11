import hashlib
import hmac
import json
import os
import time
import uuid

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("PROBUILD_API_KEY", "test-api-key-12345678")
os.environ.setdefault("PROBUILD_SIGNING_SECRET", "test-signing-secret-1234567890")

from probuild.api.app import create_app


@pytest.fixture
def client() -> TestClient:
  return TestClient(create_app())


def sign_request(
  *,
  secret: str,
  timestamp: str,
  request_id: str,
  body: bytes,
) -> str:
  body_hash = hashlib.sha256(body).hexdigest()
  message = f"{timestamp}:{request_id}:{body_hash}".encode()
  return hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()


def signed_post(client: TestClient, body: dict) -> tuple[dict[str, str], bytes]:
  raw = json.dumps(body, separators=(",", ":")).encode()
  timestamp = str(int(time.time()))
  request_id = uuid.uuid4().hex
  signature = sign_request(
    secret="test-signing-secret-1234567890",
    timestamp=timestamp,
    request_id=request_id,
    body=raw,
  )
  headers = {
    "Authorization": "Bearer test-api-key-12345678",
    "X-ProBuild-Timestamp": timestamp,
    "X-ProBuild-Request-Id": request_id,
    "X-ProBuild-Signature": signature,
    "Content-Type": "application/json",
  }
  return headers, raw


def test_health(client: TestClient) -> None:
  response = client.get("/v1/health")
  assert response.status_code == 200
  payload = response.json()
  assert payload["status"] == "ok"
  assert payload["model_loaded"] is False


def test_models(client: TestClient) -> None:
  response = client.get("/v1/models")
  assert response.status_code == 200
  models = response.json()
  assert models[0]["id"] == "probuild-base"


def test_generation_requires_auth(client: TestClient) -> None:
  response = client.post("/v1/generation", json={"prompt": "tower"})
  assert response.status_code == 401


def test_generation_invalid_signature(client: TestClient) -> None:
  body = {"prompt": "tower", "seed": 1, "width": 8, "height": 8, "depth": 8}
  headers, raw = signed_post(client, body)
  headers["X-ProBuild-Signature"] = "deadbeef"
  response = client.post("/v1/generation", content=raw, headers=headers)
  assert response.status_code == 401


def test_generation_expired_timestamp(client: TestClient) -> None:
  body = {"prompt": "tower", "seed": 1, "width": 8, "height": 8, "depth": 8}
  raw = json.dumps(body, separators=(",", ":")).encode()
  request_id = uuid.uuid4().hex
  timestamp = str(int(time.time()) - 10_000)
  signature = sign_request(
    secret="test-signing-secret-1234567890",
    timestamp=timestamp,
    request_id=request_id,
    body=raw,
  )
  headers = {
    "Authorization": "Bearer test-api-key-12345678",
    "X-ProBuild-Timestamp": timestamp,
    "X-ProBuild-Request-Id": request_id,
    "X-ProBuild-Signature": signature,
    "Content-Type": "application/json",
  }
  response = client.post("/v1/generation", content=raw, headers=headers)
  assert response.status_code == 401


def test_generation_replay(client: TestClient) -> None:
  body = {"prompt": "tower", "seed": 1, "width": 8, "height": 8, "depth": 8}
  headers, raw = signed_post(client, body)
  first = client.post("/v1/generation", content=raw, headers=headers)
  assert first.status_code in {409, 503}
  second = client.post("/v1/generation", content=raw, headers=headers)
  assert second.status_code == 409


def test_generation_model_unavailable(client: TestClient) -> None:
  body = {"prompt": "tower", "seed": 1, "width": 8, "height": 8, "depth": 8}
  headers, raw = signed_post(client, body)
  response = client.post("/v1/generation", content=raw, headers=headers)
  assert response.status_code == 503
