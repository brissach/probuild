# Probuild

Probuild turns a text prompt into a Minecraft structure. A player runs `/probuild create a small stone tower` on a Paper server. The plugin sends that prompt to a Python backend, which runs it through an ML pipeline and returns a list of blocks. The plugin validates the response and places it in the world at the player's location.

You need both halves running: the backend (FastAPI + PyTorch) and the plugin on your server. They talk over HTTP with signed requests so random clients can't hit your generation endpoint.

## What happens on a generate

1. The plugin builds a signed POST to `/v1/generation` with the prompt, seed, and structure dimensions.
2. The backend checks the signature, rate limits, and input bounds.
3. If a model checkpoint is loaded, the generation service runs the pipeline: text encoding, transformer sampling, vector quantization decode, voxel output.
4. The structure is validated (dimensions, block IDs, coordinate bounds) before it leaves the API.
5. The plugin receives JSON, validates again on its side, then places blocks on the main thread. Network I/O stays async.

Without a trained checkpoint the API still starts. Health and model listing work. Generation returns `503 MODEL_UNAVAILABLE` until you export weights and set `PROBUILD_MODEL_PATH`.

## Layout

```
backend/   FastAPI app, ML code, training scripts
plugin/    Paper plugin (package io.brissach.probuild)
```

The backend is layered: routes call application services, services call domain logic and the ML registry. The plugin keeps HTTP, command handling, validation, and world placement in separate packages. ML components implement protocols so you can swap the text encoder or generator later without touching the API surface.

## Backend setup

Python 3.11 or newer. Redis is optional; it caches identical generation requests when `PROBUILD_REDIS_URL` is set.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env
```

Edit `.env`. These matter for local dev:

| Variable | Purpose |
|----------|---------|
| `PROBUILD_API_KEY` | Bearer token the plugin sends |
| `PROBUILD_SIGNING_SECRET` | Shared HMAC secret (16+ chars) |
| `PROBUILD_MODEL_PATH` | Path to exported `.pt` artifact, or leave empty |
| `PROBUILD_MAX_STRUCTURE_SIZE` | Cap on block count per structure |
| `PROBUILD_GENERATION_TIMEOUT` | Seconds before a generate times out |

Start the server:

```bash
uvicorn probuild.api.app:create_app --factory --host 0.0.0.0 --port 8000
```

From the repo root, `make dev-backend` does the same with reload enabled. Check `http://localhost:8000/v1/health`.

### Models and training

The default model id is `probuild-base@0.1.0`. Aliases `latest`, `stable`, and `experimental` resolve to the same entry in the registry.

This repo ships the training code and inference stack, not pretrained weights. To actually generate structures you need a checkpoint:

```bash
probuild-train --data path/to/structures.npz --epochs 50
probuild-export --checkpoint artifacts/checkpoints/epoch_50.pt \
  --output artifacts/models/probuild-base-0.1.0.pt
```

Then set `PROBUILD_MODEL_PATH` to that file and restart the API.

Training datasets are `.npz` or `.npy` files containing prompts and voxel arrays. The loader interface lives in `backend/src/probuild/ml/training/datasets.py`. Schematic import isn't wired up yet, but the dataset abstraction is meant to grow that way.

Evaluate a checkpoint:

```bash
probuild-evaluate --data path/to/structures.npz --checkpoint artifacts/checkpoints/epoch_50.pt
```

### API endpoints

| Method | Path | Auth | Notes |
|--------|------|------|-------|
| GET | `/v1/health` | no | Uptime, version, whether a model is loaded |
| GET | `/v1/models` | no | Registered models and load status |
| GET | `/v1/models/{id}` | no | Single model metadata |
| POST | `/v1/generation` | yes | Returns block list + metadata |

Prometheus metrics are at `/metrics`.

### Backend tests

```bash
cd backend
pytest
ruff check src tests
mypy src
```

`make test` from the repo root runs backend and plugin tests together.

## Plugin setup

JDK 21+, Paper 1.21+.

```bash
cd plugin
./gradlew build
```

Install `plugin/build/libs/Probuild-*.jar` on your server. On first run it writes `plugins/Probuild/config.yml`:

```yaml
backend:
  url: "http://localhost:8000"
  api-key: "match your PROBUILD_API_KEY"
  signing-secret: "match your PROBUILD_SIGNING_SECRET"
  timeout-ms: 30000

generation:
  max-width: 32
  max-height: 32
  max-depth: 32
  max-concurrent-generations: 2

placement:
  max-blocks: 50000
  backend: auto
```

The api-key and signing-secret must match the backend `.env` exactly.

### Commands

| Command | Permission | What it does |
|---------|------------|--------------|
| `/probuild create <prompt>` | `probuild.create` | Generate and place at your feet |
| `/probuild reload` | `probuild.reload` | Reload config, rebind API client and placement |
| `/probuild status` | none | Backend reachability, placement mode, active jobs |

Generation runs on a small thread pool so the server doesn't stall. Block writes always happen on the main thread.

### WorldEdit

WorldEdit is a soft dependency. With it installed and `placement.backend: auto`, Probuild uses WorldEdit's `EditSession` for batch placement, which handles large structures better than setting blocks one at a time. Set `paper` to force vanilla placement, or `worldedit` to require it (falls back to paper if missing).

## Security

Generation requests are authenticated, not just signed with a static secret in the URL.

The plugin sends:

- `Authorization: Bearer <api-key>`
- `X-ProBuild-Timestamp` (unix seconds)
- `X-ProBuild-Request-Id` (unique per request)
- `X-ProBuild-Signature` (HMAC-SHA256 over timestamp, request id, and SHA-256 of the body)

The backend rejects requests with bad keys, expired timestamps (>5 min by default), invalid signatures, or duplicate request ids. Rate limiting applies per client IP.

Header names still use `X-ProBuild-*` from the original API design. Only display names changed to Probuild.

## Docker

```bash
docker compose up --build
```

Brings up the backend and Redis. Mount trained weights into `backend/artifacts/` or bake them into the image for production. Docker isn't needed for day-to-day development.
