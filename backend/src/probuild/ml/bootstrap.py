from datetime import UTC, datetime
from pathlib import Path

import torch

from probuild.domain.generation.enums import ModelArchitecture
from probuild.domain.structures.blocks import default_block_registry
from probuild.infrastructure.config.settings import Settings
from probuild.ml.inference.generator import ProbuildGenerator
from probuild.ml.models.structure_transformer import StructureTransformer
from probuild.ml.models.vector_quantizer import VectorQuantizer
from probuild.ml.models.voxel_autoencoder import VoxelAutoencoder
from probuild.ml.registry.model_metadata import ModelMetadata
from probuild.ml.registry.model_registry import ModelRegistry
from probuild.ml.text.encoder import HashTextEncoder


def build_model_registry(settings: Settings) -> ModelRegistry:
  registry = ModelRegistry()
  metadata = ModelMetadata(
    id="probuild-base",
    version=settings.model_version,
    architecture=ModelArchitecture.PROBUILD_BASE.value,
    checkpoint=None,
    created_at=datetime.now(tz=UTC),
    metadata={"device": settings.device},
  )
  registry.register(metadata, aliases=("probuild-base", "latest", "stable", "experimental"))
  if settings.model_path:
    registry.load_checkpoint("probuild-base", Path(settings.model_path), settings.device)
  return registry


def build_generator(settings: Settings, registry: ModelRegistry) -> ProbuildGenerator | None:
  if not settings.model_path or not registry.is_available("probuild-base"):
    return None

  block_registry = default_block_registry()
  device = torch.device(settings.device)
  num_blocks = block_registry.size

  text_encoder = HashTextEncoder(embedding_dim=256).to(device)
  autoencoder = VoxelAutoencoder(num_blocks=num_blocks, input_size=(32, 32, 32)).to(device)
  quantizer = VectorQuantizer(num_embeddings=512, embedding_dim=256).to(device)
  transformer = StructureTransformer(
    vocab_size=512,
    embedding_dim=256,
    num_layers=4,
    num_heads=8,
    feedforward_dim=512,
    max_sequence_length=128,
    conditioning_dim=256,
  ).to(device)

  state = registry.get_state_dict("probuild-base")
  combined = torch.nn.ModuleDict({
    "text_encoder": text_encoder,
    "autoencoder": autoencoder,
    "quantizer": quantizer,
    "transformer": transformer,
  })
  combined.load_state_dict(state, strict=False)

  return ProbuildGenerator(
    text_encoder=text_encoder,
    transformer=transformer,
    autoencoder=autoencoder,
    quantizer=quantizer,
    block_registry=block_registry,
    device=device,
  )
