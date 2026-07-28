# Probuild

**Text-to-structure generation for Minecraft.**

Probuild lets players describe a building in plain language and have it appear in the world. A Paper plugin handles commands and block placement; a Python backend runs the ML model and returns a validated 3D structure. The two halves talk over a signed HTTP API so only your server can call generation.

```
Player: /probuild create a small stone tower with windows
                    │
                    ▼
         ┌──────────────────────┐
         │   Paper plugin       │  async HTTP, main-thread placement
         │   io.brissach.probuild│
         └──────────┬───────────┘
                    │ POST /v1/generation
                    ▼
         ┌──────────────────────┐
         │   FastAPI backend    │  auth, validation, rate limits
         │   PyTorch pipeline   │
         └──────────┬───────────┘
                    │ JSON block list
                    ▼
              Structure placed
              at player's feet
```

## What you can do

| In-game | API |
|---------|-----|
| `/probuild create <prompt>` - generate and place at your location | `POST /v1/generation` - same pipeline, any client that signs requests |
| `/probuild status` - check backend and placement mode | `GET /v1/health` - uptime and model status |
| `/probuild reload` - hot-reload config | `GET /v1/models` - registered model versions |

Generation is asynchronous: the server keeps ticking while the backend works. Block writes always happen on the main thread.

**Note:** This repo ships the full training and inference stack, not pretrained weights. Without a checkpoint the API starts normally but generation returns `503 MODEL_UNAVAILABLE`. See [Training your own model](#training-your-own-model).

---

## Examples

### In-game

Stand where you want the structure to appear, then run:

```
/probuild create a small stone tower with narrow windows
/probuild create wooden cottage with a thatched roof
/probuild create desert temple with sandstone pillars
/probuild create modern glass office building
```

The plugin uses your player position (floored to block coordinates) as the origin. Structures are placed in a box up to the configured max dimensions (default 32×32×32).

While generating:

```
Probuild generation started...
Probuild placed 1847 blocks.
```

If the backend is down or busy:

```
Probuild generation failed: Connection refused
Probuild is busy. Try again shortly.
```

Check connectivity anytime:

```
/probuild status
Backend: online
Placement: worldedit
WorldEdit: installed
Active generations: 0
```

### API request

Generation requires a Bearer token and an HMAC signature. The plugin handles this automatically; for manual testing:

```bash
# 1. Set shared secrets (must match plugin config.yml)
export PROBUILD_API_KEY="dev-api-key-change-in-production"
export PROBUILD_SIGNING_SECRET="dev-signing-secret-change-in-production"

# 2. Build and sign the body (see backend/tests/api/test_generation.py for reference)
BODY='{"prompt":"small stone tower","seed":42,"width":16,"height":16,"depth":16}'
TS=$(date +%s)
REQ_ID=$(uuidgen | tr -d '-')
BODY_HASH=$(echo -n "$BODY" | sha256sum | awk '{print $1}')
SIG=$(echo -n "${TS}:${REQ_ID}:${BODY_HASH}" \
  | openssl dgst -sha256 -hmac "$PROBUILD_SIGNING_SECRET" | awk '{print $2}')

curl -s http://localhost:8000/v1/generation \
  -H "Authorization: Bearer $PROBUILD_API_KEY" \
  -H "X-ProBuild-Timestamp: $TS" \
  -H "X-ProBuild-Request-Id: $REQ_ID" \
  -H "X-ProBuild-Signature: $SIG" \
  -H "Content-Type: application/json" \
  -d "$BODY" | jq
```

Example response (truncated):

```json
{
  "generation_id": "gen_a1b2c3d4",
  "model": {
    "id": "probuild-base",
    "version": "0.1.0",
    "architecture": "transformer-vq-vae",
    "loaded": true
  },
  "structure": {
    "width": 16,
    "height": 16,
    "depth": 16,
    "blocks": [
      { "x": 0, "y": 0, "z": 0, "block": "stone" },
      { "x": 0, "y": 1, "z": 0, "block": "stone_bricks" }
    ]
  },
  "metadata": {
    "seed": 42,
    "duration_ms": 1240
  }
}
```

Air blocks are omitted. Coordinates are relative to the structure origin (0, 0, 0) at the placement point.

---

## How it works

### End-to-end flow

1. **Command** - Player runs `/probuild create …`. The plugin captures the prompt, a seed derived from the player UUID, and max dimensions from config.
2. **Request** - The plugin POSTs to `/v1/generation` with signed headers. Network I/O runs off the main thread.
3. **Backend checks** - API key, HMAC signature, timestamp freshness, replay protection, rate limits, and input bounds.
4. **Generation** - If a model is loaded, the ML pipeline produces a voxel structure (see below).
5. **Validation** - The backend validates dimensions, block IDs, and coordinate bounds. The plugin validates again before placing.
6. **Placement** - Blocks are written on the main thread via Paper or WorldEdit (`placement.backend: auto|paper|worldedit`).

### ML pipeline

Probuild treats structure generation as **conditional token sampling** followed by **voxel decoding**:

```
prompt ──► TextEncoder ──► conditioning vector
                              │
                              ▼
                    StructureTransformer
                    (autoregressive sampling)
                              │
                              ▼
                    VectorQuantizer indices
                              │
                              ▼
                    VoxelAutoencoder decode
                              │
                              ▼
                    block ID per cell ──► Structure
```

| Stage | Role |
|-------|------|
| **Text encoder** | Maps the prompt to a fixed-size conditioning vector |
| **Structure transformer** | Samples a sequence of discrete tokens (temperature, top-k, top-p configurable) |
| **Vector quantizer** | Converts token indices back to latent embeddings |
| **Voxel autoencoder** | Decodes latents into a 3D grid of block logits; argmax → block IDs |

The default model id is `probuild-base@0.1.0`. Aliases `latest`, `stable`, and `experimental` resolve through the model registry.

### Project layout

```
backend/          FastAPI app, ML models, training scripts, tests
plugin/           Paper plugin (package io.brissach.probuild)
docker-compose.yml   Backend + Redis for production-style deploys
```

Both halves are layered so you can swap components (text encoder, placement backend, cache) without rewriting the surface API.

---

## Quick start

You need **both** the backend and the plugin running with matching credentials.

### 1. Backend

Requirements: Python 3.11+, optional Redis for response caching.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env
```

Edit `.env` - at minimum set `PROBUILD_API_KEY` and `PROBUILD_SIGNING_SECRET` (16+ characters each).

```bash
uvicorn probuild.api.app:create_app --factory --host 0.0.0.0 --port 8000
# or from repo root:
make dev-backend
```

Verify: `curl http://localhost:8000/v1/health`

### 2. Plugin

Requirements: JDK 21+, Paper 1.21+.

```bash
cd plugin
./gradlew build        # Windows: gradlew.bat build
```

Copy `plugin/build/libs/Probuild-*.jar` into your server's `plugins/` folder. On first start, edit `plugins/Probuild/config.yml`:

```yaml
backend:
  url: "http://localhost:8000"
  api-key: "same as PROBUILD_API_KEY"
  signing-secret: "same as PROBUILD_SIGNING_SECRET"
  timeout-ms: 30000

generation:
  max-width: 32
  max-height: 32
  max-depth: 32
  max-concurrent-generations: 2

placement:
  max-blocks: 50000
  backend: auto    # auto | paper | worldedit
```

Restart the server (or `/probuild reload` after editing config).

### 3. Try it

```
/probuild status
/probuild create a small stone tower
```

---

## Configuration reference

### Backend (`.env`)

| Variable | Purpose |
|----------|---------|
| `PROBUILD_API_KEY` | Bearer token the plugin sends |
| `PROBUILD_SIGNING_SECRET` | Shared HMAC secret (16+ chars) |
| `PROBUILD_MODEL_PATH` | Path to exported `.pt` artifact; empty = no generation |
| `PROBUILD_DEVICE` | `cpu` or `cuda` |
| `PROBUILD_REDIS_URL` | Optional cache for identical requests |
| `PROBUILD_MAX_STRUCTURE_SIZE` | Max blocks per structure |
| `PROBUILD_GENERATION_TIMEOUT` | Seconds before a generate times out |
| `PROBUILD_RATE_LIMIT_PER_MINUTE` | Per-IP rate limit |

### Plugin (`config.yml`)

| Key | Purpose |
|-----|---------|
| `backend.url` | API base URL |
| `backend.api-key` / `signing-secret` | Must match backend exactly |
| `generation.max-*` | Structure bounds sent to the API |
| `generation.max-concurrent-generations` | Thread pool + semaphore limit |
| `placement.max-blocks` | Reject structures larger than this |
| `placement.backend` | `auto` prefers WorldEdit when installed |

### Permissions

| Permission | Default | Command |
|------------|---------|---------|
| `probuild.create` | op | `/probuild create` |
| `probuild.reload` | op | `/probuild reload` |
| *(none)* | everyone | `/probuild status` |

---

## Training your own model

Probuild ships CLI tools for training, evaluation, and export. You provide paired **prompts + 3D voxel grids**; the current training loop fits the **voxel autoencoder** (reconstruction loss). Prompts are stored in the dataset format for future transformer training but are not used by `probuild-train` yet.

```
structures.npz  ──► probuild-train  ──► checkpoints/epoch_N.pt
                                              │
                                              ▼
                                    probuild-export  ──► probuild-base-0.1.0.pt
                                              │
                                              ▼
                              PROBUILD_MODEL_PATH + API restart
```

### What data you need

Each training sample is one structure with:

| Field | Type | Description |
|-------|------|-------------|
| `prompt` | string | Human description shown to the model at inference time (e.g. `"small stone tower with windows"`) |
| `voxels` | float32 array | One-hot encoded 3D grid - see shape below |
| `metadata` | dict (optional) | Anything you want to keep alongside the sample (source schematic, author, tags) |

**Voxel tensor shape:** `(num_blocks, width, height, depth)` - default `(16, 32, 32, 32)`.

Each spatial cell `(x, y, z)` has exactly one channel set to `1.0` (the block type at that cell). All other channels are `0.0`. Air is a valid block type and is typically the majority of cells.

Structures should be **origin-aligned**: build content starting at `(0, 0, 0)` within the grid. Anything outside the 32×32×32 cube is clipped.

### Supported block palette

Training and inference share the default block registry (`backend/src/probuild/domain/structures/blocks.py`). Voxel channel index maps to block ID:

| Index | Block ID | Index | Block ID |
|-------|----------|-------|----------|
| 0 | `air` | 8 | `bricks` |
| 1 | `stone` | 9 | `dirt` |
| 2 | `cobblestone` | 10 | `grass_block` |
| 3 | `stone_bricks` | 11 | `sand` |
| 4 | `oak_planks` | 12 | `spruce_planks` |
| 5 | `oak_log` | 13 | `spruce_log` |
| 6 | `oak_leaves` | 14 | `water` |
| 7 | `glass` | 15 | `torch` |

Blocks outside this palette must be mapped or skipped when building your dataset. Schematic import is not wired up yet, but the dataset loader is designed to grow that way.

### Dataset file formats

#### `.npz` (recommended - used by `probuild-train`)

A NumPy archive with three arrays:

| Key | Shape | Dtype | Notes |
|-----|-------|-------|-------|
| `prompts` | `(N,)` | object (strings) | One prompt per sample |
| `voxels` | `(N, 16, 32, 32, 32)` | float32 | One-hot grids stacked |
| `metadata` | `(N,)` | object (dicts) | Optional; defaults to `{}` |

#### `.npy` (alternative)

A single object array where each element is a dict:

```python
{"prompt": "...", "voxels": ndarray, "metadata": {...}}
```

Load with `load_npy_dataset()` in `datasets.py`. The train script currently calls `load_npz_dataset()` only.

### Building a dataset

Convert block-index grids to one-hot tensors with the helper in `backend/src/probuild/ml/structures/voxelizer.py`:

```python
import numpy as np
import torch
from probuild.domain.structures.blocks import default_block_registry
from probuild.ml.structures.voxelizer import one_hot_voxels

registry = default_block_registry()
num_blocks = registry.size  # 16

# voxel_indices: int array shaped (depth, height, width), values 0..15
# 0 = air, 1 = stone, etc. - see palette table above
voxel_indices = np.zeros((32, 32, 32), dtype=np.int64)
voxel_indices[0:8, 0:4, 0:4] = registry.index_of("stone")  # example footprint

one_hot = one_hot_voxels(voxel_indices, num_blocks=num_blocks)
# one_hot shape: (1, 16, 32, 32, 32) - squeeze(0) for a single sample
sample_voxels = one_hot.squeeze(0).numpy()
```

Assemble many samples into an `.npz`:

```python
import numpy as np

prompts = [
    "small stone tower with narrow windows",
    "wooden cottage with a thatched roof",
]
voxels = np.stack([sample_voxels_1, sample_voxels_2])  # (N, 16, 32, 32, 32)
metadata = [{"source": "manual"}, {"source": "manual"}]

np.savez("structures.npz", prompts=np.array(prompts, dtype=object), voxels=voxels, metadata=np.array(metadata, dtype=object))
```

**Tips for good training data:**

- Use **consistent prompts** - describe style, materials, and size the way players will type them in-game.
- Include **diverse structures** (houses, towers, bridges) but keep them within the 32³ bounds.
- Prefer **dense structures** over mostly-air grids; the autoencoder learns faster when non-air voxels carry signal.
- Hold out 10-20% of samples for evaluation with `probuild-evaluate`.
- More samples help, but even a small curated set (50-100) is enough to smoke-test the pipeline.

### Train

```bash
probuild-train \
  --data path/to/structures.npz \
  --epochs 50 \
  --batch-size 4 \
  --device cpu \
  --checkpoint-dir artifacts/checkpoints
```

| Flag | Default | Description |
|------|---------|-------------|
| `--data` | *(required)* | Path to `.npz` dataset |
| `--epochs` | `10` | Training epochs |
| `--batch-size` | `4` | Batch size |
| `--device` | `cpu` | `cpu` or `cuda` |
| `--checkpoint-dir` | `artifacts/checkpoints` | Where `epoch_N.pt` files are written |

Each epoch saves a checkpoint containing `state_dict`, `epoch`, and `loss`. Training minimizes MSE between input voxels and the autoencoder reconstruction.

### Evaluate

```bash
probuild-evaluate \
  --data path/to/structures.npz \
  --checkpoint artifacts/checkpoints/epoch_50.pt \
  --device cpu
```

Prints `average_loss=` - mean reconstruction MSE across all samples. Use this to compare checkpoints and catch overfitting on your holdout set.

### Export for inference

```bash
probuild-export \
  --checkpoint artifacts/checkpoints/epoch_50.pt \
  --output artifacts/models/probuild-base-0.1.0.pt \
  --device cpu
```

Bundles the full inference stack (text encoder, autoencoder, vector quantizer, transformer) into a single artifact. Weights from the training checkpoint are merged in; modules not present in the checkpoint keep their initialized parameters.

### Deploy the trained model

```bash
# In backend/.env
PROBUILD_MODEL_PATH=artifacts/models/probuild-base-0.1.0.pt
PROBUILD_DEVICE=cpu   # or cuda
```

Restart the API and confirm:

```bash
curl http://localhost:8000/v1/health
# "model_loaded": true
```

Then test in-game: `/probuild create a small stone tower`.

**Current limitation:** only the autoencoder is trained from your data today. The transformer and text encoder use their default initialization at export time, so prompt-conditioned generation quality will improve as end-to-end training lands. The voxel autoencoder checkpoint still enables the full pipeline to load and run.

---

## WorldEdit integration

WorldEdit is a **soft dependency**. With it installed and `placement.backend: auto`, Probuild uses an `EditSession` for batch placement - much faster for large structures than setting blocks one at a time.

| Value | Behavior |
|-------|----------|
| `auto` | WorldEdit if present, otherwise Paper |
| `paper` | Always vanilla block placement |
| `worldedit` | Require WorldEdit; fall back to Paper if missing |

---

## Security

Generation is authenticated **and** signed - a static secret in the URL is not enough.

Every request includes:

- `Authorization: Bearer <api-key>`
- `X-ProBuild-Timestamp` - rejected if older than 5 minutes (configurable)
- `X-ProBuild-Request-Id` - unique; replays are rejected
- `X-ProBuild-Signature` - HMAC-SHA256 over `timestamp:request_id:sha256(body)`

The backend also rate-limits by client IP. Header names retain the `X-ProBuild-*` prefix from the original API design.

---

## API reference

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/v1/health` | no | Status, version, `model_loaded` |
| GET | `/v1/models` | no | All registered models |
| GET | `/v1/models/{id}` | no | Single model metadata |
| POST | `/v1/generation` | yes | Generate structure from prompt |
| GET | `/metrics` | no | Prometheus metrics |

### Generation request body

| Field | Default | Range | Notes |
|-------|---------|-------|-------|
| `prompt` | - | 1-512 chars | Required |
| `seed` | `0` | 0-2147483647 | Reproducibility |
| `width`, `height`, `depth` | `32` | 1-64 | Structure bounds |
| `temperature` | `0.8` | 0.0-2.0 | Sampling randomness |
| `top_k` | `50` | 0-512 | Top-k filtering |
| `top_p` | `1.0` | 0.0-1.0 | Nucleus sampling |
| `model` | registry default | - | Optional model id |

---

## Development

```bash
make test            # backend pytest + plugin gradle test
make lint            # ruff
make typecheck       # mypy
make build-plugin    # produce plugin JAR
make docker-up       # backend + Redis via Docker Compose
```

Backend tests live in `backend/tests/`. Plugin tests cover signing, structure validation, serialization, and the command framework.

### Docker

```bash
docker compose up --build
```

Brings up the backend and Redis. Mount trained weights into `backend/artifacts/` or bake them into the image for production. Docker is optional for local development.

---

## Requirements summary

| Component | Version |
|-----------|---------|
| Python | 3.11+ |
| JDK | 21+ |
| Paper | 1.21+ |
| WorldEdit | optional |
| Redis | optional (caching) |
