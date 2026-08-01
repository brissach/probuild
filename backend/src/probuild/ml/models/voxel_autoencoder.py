import torch
import torch.nn as nn
import torch.nn.functional as F


class VoxelEncoder(nn.Module):
  def __init__(
    self,
    *,
    num_blocks: int,
    input_size: tuple[int, int, int],
    channels: tuple[int, ...],
    latent_dim: int,
  ) -> None:
    super().__init__()
    self.input_size = input_size
    self.latent_dim = latent_dim
    layers: list[nn.Module] = []
    in_channels = num_blocks
    for out_channels in channels:
      layers.extend([
        nn.Conv3d(in_channels, out_channels, kernel_size=3, stride=2, padding=1),
        nn.GroupNorm(min(8, out_channels), out_channels),
        nn.GELU(),
      ])
      in_channels = out_channels
    self.conv = nn.Sequential(*layers)
    with torch.no_grad():
      dummy = torch.zeros(1, num_blocks, *input_size)
      flat_dim = self.conv(dummy).view(1, -1).shape[1]
    self.proj = nn.Linear(flat_dim, latent_dim)

  def forward(self, voxels: torch.Tensor) -> torch.Tensor:
    encoded = self.conv(voxels)
    return self.proj(encoded.view(encoded.size(0), -1))


class VoxelDecoder(nn.Module):
  def __init__(
    self,
    *,
    num_blocks: int,
    output_size: tuple[int, int, int],
    channels: tuple[int, ...],
    latent_dim: int,
    encoder_flat_dim: int,
  ) -> None:
    super().__init__()
    self.output_size = output_size
    reversed_channels = tuple(reversed(channels))
    start_channels = reversed_channels[0]
    self.start_channels = start_channels
    self.fc = nn.Linear(latent_dim, encoder_flat_dim)
    self.encoder_flat_dim = encoder_flat_dim
    self.start_shape = self._infer_start_shape(encoder_flat_dim, start_channels)

    layers: list[nn.Module] = []
    in_channels = start_channels
    for out_channels in reversed_channels[1:]:
      layers.extend([
        nn.ConvTranspose3d(in_channels, out_channels, kernel_size=4, stride=2, padding=1),
        nn.GroupNorm(min(8, out_channels), out_channels),
        nn.GELU(),
      ])
      in_channels = out_channels
    layers.append(nn.ConvTranspose3d(in_channels, num_blocks, kernel_size=4, stride=2, padding=1))
    self.deconv = nn.Sequential(*layers)

  def _infer_start_shape(self, flat_dim: int, channels: int) -> tuple[int, int, int]:
    spatial = int(round((flat_dim / channels) ** (1 / 3)))
    spatial = max(1, spatial)
    while channels * spatial ** 3 < flat_dim:
      spatial += 1
    return (spatial, spatial, spatial)

  def forward(self, latent: torch.Tensor) -> torch.Tensor:
    x = self.fc(latent)
    x = x.view(x.size(0), self.start_channels, *self.start_shape)
    x = self.deconv(x)
    return F.interpolate(x, size=self.output_size, mode="trilinear", align_corners=False)


class VoxelAutoencoder(nn.Module):
  def __init__(
    self,
    *,
    num_blocks: int,
    input_size: tuple[int, int, int] = (32, 32, 32),
    channels: tuple[int, ...] = (32, 64, 128),
    latent_dim: int = 256,
  ) -> None:
    super().__init__()
    self.encoder = VoxelEncoder(
      num_blocks=num_blocks,
      input_size=input_size,
      channels=channels,
      latent_dim=latent_dim,
    )
    with torch.no_grad():
      encoder_flat = self.encoder.conv(
        torch.zeros(1, num_blocks, *input_size),
      ).view(1, -1).shape[1]
    self.decoder = VoxelDecoder(
      num_blocks=num_blocks,
      output_size=input_size,
      channels=channels,
      latent_dim=latent_dim,
      encoder_flat_dim=encoder_flat,
    )
    self.latent_dim = latent_dim

  def encode(self, voxels: torch.Tensor) -> torch.Tensor:
    return self.encoder(voxels)

  def decode(self, latent: torch.Tensor) -> torch.Tensor:
    return self.decoder(latent)

  def forward(self, voxels: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    latent = self.encode(voxels)
    reconstruction = self.decode(latent)
    return reconstruction, latent
