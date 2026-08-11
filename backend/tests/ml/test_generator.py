import torch

from probuild.domain.generation.models import GenerationConfig
from probuild.domain.structures.blocks import default_block_registry
from probuild.ml.inference.generator import ProbuildGenerator
from probuild.ml.models.structure_transformer import StructureTransformer
from probuild.ml.models.vector_quantizer import VectorQuantizer
from probuild.ml.models.voxel_autoencoder import VoxelAutoencoder
from probuild.ml.text.encoder import HashTextEncoder


def test_deterministic_generation() -> None:
  block_registry = default_block_registry()
  device = torch.device("cpu")
  text_encoder = HashTextEncoder(embedding_dim=256)
  autoencoder = VoxelAutoencoder(num_blocks=block_registry.size)
  quantizer = VectorQuantizer(num_embeddings=512, embedding_dim=256)
  transformer = StructureTransformer(
    vocab_size=512,
    embedding_dim=256,
    num_layers=2,
    num_heads=4,
    feedforward_dim=256,
    max_sequence_length=32,
    conditioning_dim=256,
  )
  generator = ProbuildGenerator(
    text_encoder=text_encoder,
    transformer=transformer,
    autoencoder=autoencoder,
    quantizer=quantizer,
    block_registry=block_registry,
    device=device,
  )
  config = GenerationConfig(
    seed=12345,
    width=8,
    height=8,
    depth=8,
    temperature=0.0,
    top_k=0,
    top_p=1.0,
    max_tokens=16,
  )
  first = generator.generate("stone tower", config)
  second = generator.generate("stone tower", config)
  assert first.block_count == second.block_count
  assert {(b.coordinate.x, b.coordinate.y, b.coordinate.z, b.block_id) for b in first.blocks} == {
    (b.coordinate.x, b.coordinate.y, b.coordinate.z, b.block_id) for b in second.blocks
  }
