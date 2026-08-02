
import torch
import torch.nn as nn


class StructureTransformer(nn.Module):
  def __init__(
    self,
    *,
    vocab_size: int,
    embedding_dim: int,
    num_layers: int,
    num_heads: int,
    feedforward_dim: int,
    max_sequence_length: int,
    conditioning_dim: int,
    dropout: float = 0.1,
  ) -> None:
    super().__init__()
    self.max_sequence_length = max_sequence_length
    self.token_embedding = nn.Embedding(vocab_size, embedding_dim)
    self.pos_embedding = nn.Embedding(max_sequence_length, embedding_dim)
    self.condition_proj = nn.Linear(conditioning_dim, embedding_dim)
    encoder_layer = nn.TransformerEncoderLayer(
      d_model=embedding_dim,
      nhead=num_heads,
      dim_feedforward=feedforward_dim,
      dropout=dropout,
      batch_first=True,
      activation="gelu",
    )
    self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
    self.output = nn.Linear(embedding_dim, vocab_size)
    self.dropout = nn.Dropout(dropout)
    self._register_causal_mask(max_sequence_length)

  def _register_causal_mask(self, length: int) -> None:
    mask = torch.triu(torch.ones(length, length), diagonal=1).bool()
    self.register_buffer("causal_mask", mask, persistent=False)

  def forward(
    self,
    token_ids: torch.Tensor,
    conditioning: torch.Tensor,
  ) -> torch.Tensor:
    batch, seq_len = token_ids.shape
    positions = torch.arange(seq_len, device=token_ids.device).unsqueeze(0).expand(batch, -1)
    x = self.token_embedding(token_ids) + self.pos_embedding(positions)
    cond = self.condition_proj(conditioning).unsqueeze(1)
    x = self.dropout(x + cond)
    mask = self.causal_mask[:seq_len, :seq_len]
    hidden = self.transformer(x, mask=mask, is_causal=True)
    return self.output(hidden)

  def init_sequence(self, batch_size: int, device: torch.device) -> torch.Tensor:
    return torch.zeros((batch_size, 1), dtype=torch.long, device=device)
