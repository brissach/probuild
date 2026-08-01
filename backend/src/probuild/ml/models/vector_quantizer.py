import torch
import torch.nn as nn
import torch.nn.functional as F


class VectorQuantizer(nn.Module):
  def __init__(
    self,
    *,
    num_embeddings: int,
    embedding_dim: int,
    commitment_cost: float = 0.25,
  ) -> None:
    super().__init__()
    self.num_embeddings = num_embeddings
    self.embedding_dim = embedding_dim
    self.commitment_cost = commitment_cost
    self.embeddings = nn.Embedding(num_embeddings, embedding_dim)
    nn.init.uniform_(self.embeddings.weight, -1.0 / num_embeddings, 1.0 / num_embeddings)

  def forward(self, inputs: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    flat = inputs.reshape(-1, self.embedding_dim)
    distances = (
      flat.pow(2).sum(dim=1, keepdim=True)
      + self.embeddings.weight.pow(2).sum(dim=1)
      - 2 * flat @ self.embeddings.weight.t()
    )
    indices = distances.argmin(dim=1)
    quantized = self.embeddings(indices).view_as(inputs)

    codebook_loss = F.mse_loss(quantized.detach(), inputs)
    commitment_loss = F.mse_loss(quantized, inputs.detach())
    loss = codebook_loss + self.commitment_cost * commitment_loss

    quantized_st = inputs + (quantized - inputs).detach()
    return quantized_st, loss, indices.view(inputs.shape[:-1])

  def decode_indices(self, indices: torch.Tensor) -> torch.Tensor:
    return self.embeddings(indices)
