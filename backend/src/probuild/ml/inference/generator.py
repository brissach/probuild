import torch

from probuild.domain.generation.models import GenerationConfig
from probuild.domain.structures.blocks import BlockRegistry
from probuild.domain.structures.bounds import StructureBounds
from probuild.domain.structures.coordinates import BlockCoordinate
from probuild.domain.structures.models import BlockPlacement, Structure
from probuild.ml.inference.sampler import SamplingConfig, build_sampler
from probuild.ml.models.structure_transformer import StructureTransformer
from probuild.ml.models.vector_quantizer import VectorQuantizer
from probuild.ml.models.voxel_autoencoder import VoxelAutoencoder
from probuild.ml.text.encoder import TextEncoder


class StructureDecoder:
  def __init__(
    self,
    *,
    autoencoder: VoxelAutoencoder,
    quantizer: VectorQuantizer,
    block_registry: BlockRegistry,
  ) -> None:
    self._autoencoder = autoencoder
    self._quantizer = quantizer
    self._block_registry = block_registry

  def decode_latent(self, latent: torch.Tensor, bounds: StructureBounds) -> Structure:
    voxels = self._autoencoder.decode(latent)
    return self._voxels_to_structure(voxels[0], bounds)

  def decode_tokens(self, tokens: torch.Tensor, bounds: StructureBounds) -> Structure:
    embeddings = self._quantizer.decode_indices(tokens)
    pooled = embeddings.mean(dim=1)
    return self.decode_latent(pooled, bounds)

  def _voxels_to_structure(self, logits: torch.Tensor, bounds: StructureBounds) -> Structure:
    indices = torch.argmax(logits, dim=0)
    placements: list[BlockPlacement] = []
    for x in range(bounds.width):
      for y in range(bounds.height):
        for z in range(bounds.depth):
          block_idx = int(indices[x, y, z].item())
          block_id = self._block_registry.id_at(block_idx)
          if block_id == "air":
            continue
          placements.append(
            BlockPlacement(
              coordinate=BlockCoordinate(x=x, y=y, z=z),
              block_id=block_id,
            ),
          )
    return Structure(bounds=bounds, blocks=tuple(placements))


class ProbuildGenerator:
  def __init__(
    self,
    *,
    text_encoder: TextEncoder,
    transformer: StructureTransformer,
    autoencoder: VoxelAutoencoder,
    quantizer: VectorQuantizer,
    block_registry: BlockRegistry,
    device: torch.device,
  ) -> None:
    self._text_encoder = text_encoder
    self._transformer = transformer
    self._decoder = StructureDecoder(
      autoencoder=autoencoder,
      quantizer=quantizer,
      block_registry=block_registry,
    )
    self._quantizer = quantizer
    self._device = device
    self._vocab_size = transformer.output.out_features

  def generate(self, prompt: str, config: GenerationConfig) -> Structure:
    torch.manual_seed(config.seed)
    bounds = StructureBounds(width=config.width, height=config.height, depth=config.depth)
    conditioning = self._text_encoder.encode(prompt).to(self._device).unsqueeze(0)

    sampling = SamplingConfig(
      temperature=config.temperature,
      top_k=config.top_k,
      top_p=config.top_p,
    )
    sampler = build_sampler(sampling)

    sequence = self._transformer.init_sequence(1, self._device)
    max_steps = min(config.max_tokens, self._transformer.max_sequence_length - 1)

    for _ in range(max_steps):
      logits = self._transformer(sequence, conditioning)
      next_token = sampler.sample(logits[0, -1])
      next_tensor = torch.tensor([[next_token]], device=self._device)
      sequence = torch.cat([sequence, next_tensor], dim=1)

    return self._decoder.decode_tokens(sequence[:, 1:], bounds)
