import argparse
from pathlib import Path

import torch

from probuild.domain.structures.blocks import default_block_registry
from probuild.ml.models.structure_transformer import StructureTransformer
from probuild.ml.models.vector_quantizer import VectorQuantizer
from probuild.ml.models.voxel_autoencoder import VoxelAutoencoder
from probuild.ml.text.encoder import HashTextEncoder


def main() -> None:
  parser = argparse.ArgumentParser(description="Export Probuild model artifact")
  parser.add_argument("--checkpoint", type=Path, required=True)
  parser.add_argument("--output", type=Path, required=True)
  parser.add_argument("--device", default="cpu")
  args = parser.parse_args()

  block_registry = default_block_registry()
  device = torch.device(args.device)
  modules = torch.nn.ModuleDict({
    "text_encoder": HashTextEncoder(embedding_dim=256),
    "autoencoder": VoxelAutoencoder(num_blocks=block_registry.size),
    "quantizer": VectorQuantizer(num_embeddings=512, embedding_dim=256),
    "transformer": StructureTransformer(
      vocab_size=512,
      embedding_dim=256,
      num_layers=4,
      num_heads=8,
      feedforward_dim=512,
      max_sequence_length=128,
      conditioning_dim=256,
    ),
  }).to(device)

  payload = torch.load(args.checkpoint, map_location=device, weights_only=True)
  state = payload.get("state_dict", payload)
  modules.load_state_dict(state, strict=False)

  args.output.parent.mkdir(parents=True, exist_ok=True)
  torch.save({"state_dict": modules.state_dict(), "version": "0.1.0"}, args.output)
  print(f"exported={args.output}")


if __name__ == "__main__":
  main()
