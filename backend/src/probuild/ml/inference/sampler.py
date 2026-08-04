from dataclasses import dataclass
from typing import Protocol

import torch


class TokenSampler(Protocol):
  def sample(self, logits: torch.Tensor) -> int:
    ...


@dataclass(frozen=True, slots=True)
class SamplingConfig:
  temperature: float = 1.0
  top_k: int = 0
  top_p: float = 1.0


class GreedySampler:
  def sample(self, logits: torch.Tensor) -> int:
    return int(torch.argmax(logits).item())


class TemperatureSampler:
  def __init__(self, *, temperature: float) -> None:
    self._temperature = max(temperature, 1e-5)

  def sample(self, logits: torch.Tensor) -> int:
    scaled = logits / self._temperature
    probs = torch.softmax(scaled, dim=-1)
    return int(torch.multinomial(probs, num_samples=1).item())


class TopKSampler:
  def __init__(self, *, temperature: float, top_k: int) -> None:
    self._temperature = max(temperature, 1e-5)
    self._top_k = top_k

  def sample(self, logits: torch.Tensor) -> int:
    values, indices = torch.topk(logits, min(self._top_k, logits.numel()))
    scaled = values / self._temperature
    probs = torch.softmax(scaled, dim=-1)
    choice = int(torch.multinomial(probs, num_samples=1).item())
    return int(indices[choice].item())


class TopPSampler:
  def __init__(self, *, temperature: float, top_p: float) -> None:
    self._temperature = max(temperature, 1e-5)
    self._top_p = top_p

  def sample(self, logits: torch.Tensor) -> int:
    scaled = logits / self._temperature
    sorted_logits, sorted_indices = torch.sort(scaled, descending=True)
    probs = torch.softmax(sorted_logits, dim=-1)
    cumulative = torch.cumsum(probs, dim=-1)
    cutoff = cumulative > self._top_p
    cutoff[..., 1:] = cutoff[..., :-1].clone()
    cutoff[..., 0] = False
    filtered_logits = sorted_logits.masked_fill(cutoff, float("-inf"))
    probs = torch.softmax(filtered_logits, dim=-1)
    choice = int(torch.multinomial(probs, num_samples=1).item())
    return int(sorted_indices[choice].item())


def build_sampler(config: SamplingConfig) -> TokenSampler:
  if config.temperature <= 0:
    return GreedySampler()
  if config.top_k > 0 and config.top_p < 1.0:
    return TopPSampler(temperature=config.temperature, top_p=config.top_p)
  if config.top_k > 0:
    return TopKSampler(temperature=config.temperature, top_k=config.top_k)
  if config.top_p < 1.0:
    return TopPSampler(temperature=config.temperature, top_p=config.top_p)
  return TemperatureSampler(temperature=config.temperature)
