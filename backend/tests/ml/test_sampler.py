import torch

from probuild.ml.inference.sampler import GreedySampler, SamplingConfig, TopKSampler, build_sampler
from probuild.ml.models.vector_quantizer import VectorQuantizer


def test_greedy_sampler() -> None:
  logits = torch.tensor([0.1, 0.9, 0.2])
  assert GreedySampler().sample(logits) == 1


def test_vector_quantizer_shapes() -> None:
  quantizer = VectorQuantizer(num_embeddings=32, embedding_dim=16)
  inputs = torch.randn(2, 4, 16)
  quantized, loss, indices = quantizer(inputs)
  assert quantized.shape == inputs.shape
  assert loss.ndim == 0
  assert indices.shape == (2, 4)


def test_build_sampler_top_k() -> None:
  sampler = build_sampler(SamplingConfig(temperature=1.0, top_k=2, top_p=1.0))
  assert isinstance(sampler, TopKSampler)
