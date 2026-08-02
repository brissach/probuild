import re
from typing import Protocol

import torch


class TextEncoder(Protocol):
  @property
  def embedding_dim(self) -> int:
    ...

  def encode(self, text: str) -> torch.Tensor:
    ...


class SimpleTokenizer:
  def __init__(self, *, vocab_size: int = 4096) -> None:
    self._vocab_size = vocab_size

  def tokenize(self, text: str) -> list[int]:
    tokens = re.findall(r"[a-z0-9_]+", text.lower())
    return [hash(token) % self._vocab_size for token in tokens] or [0]

  def encode(self, text: str, max_length: int = 64) -> torch.Tensor:
    ids = self.tokenize(text)[:max_length]
    padded = ids + [0] * (max_length - len(ids))
    return torch.tensor(padded, dtype=torch.long)


class HashTextEncoder(torch.nn.Module):
  def __init__(
    self,
    *,
    vocab_size: int = 4096,
    embedding_dim: int = 256,
    max_length: int = 64,
  ) -> None:
    super().__init__()
    self._max_length = max_length
    self._embedding = torch.nn.Embedding(vocab_size, embedding_dim)
    self._tokenizer = SimpleTokenizer(vocab_size=vocab_size)

  @property
  def embedding_dim(self) -> int:
    return self._embedding.embedding_dim

  def encode(self, text: str) -> torch.Tensor:
    tokens = self._tokenizer.encode(text, self._max_length)
    embedded = self._embedding(tokens)
    mask = (tokens != 0).float().unsqueeze(-1)
    summed = (embedded * mask).sum(dim=0)
    count = mask.sum().clamp(min=1.0)
    return summed / count

  def forward(self, text: str) -> torch.Tensor:
    return self.encode(text)
