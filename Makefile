.PHONY: dev-backend test test-backend test-plugin lint typecheck build-plugin docker-up

dev-backend:
  cd backend && uvicorn probuild.api.app:create_app --factory --reload --host 0.0.0.0 --port 8000

test: test-backend test-plugin

test-backend:
  cd backend && pytest -q

test-plugin:
  cd plugin && ./gradlew test

lint:
  cd backend && ruff check src tests

typecheck:
  cd backend && mypy src

build-plugin:
  cd plugin && ./gradlew build

docker-up:
  docker compose up --build
