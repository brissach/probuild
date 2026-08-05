import argparse
from pathlib import Path

import torch

from probuild.ml.models.voxel_autoencoder import VoxelAutoencoder
from probuild.ml.training.datasets import load_npz_dataset


def main() -> None:
  parser = argparse.ArgumentParser(description="Evaluate Probuild checkpoint")
  parser.add_argument("--data", type=Path, required=True)
  parser.add_argument("--checkpoint", type=Path, required=True)
  parser.add_argument("--device", default="cpu")
  args = parser.parse_args()

  dataset = load_npz_dataset(args.data)
  model = VoxelAutoencoder(num_blocks=16, input_size=(32, 32, 32)).to(args.device)
  payload = torch.load(args.checkpoint, map_location=args.device, weights_only=True)
  state = payload["state_dict"] if isinstance(payload, dict) else payload
  model.load_state_dict(state, strict=False)
  model.eval()

  total_loss = 0.0
  with torch.no_grad():
    for index in range(len(dataset)):
      sample = dataset[index]
      inputs = torch.tensor(sample.voxels, dtype=torch.float32).unsqueeze(0).to(args.device)
      reconstruction, _ = model(inputs)
      loss = torch.nn.functional.mse_loss(reconstruction, inputs)
      total_loss += float(loss.item())

  print(f"average_loss={total_loss / max(len(dataset), 1):.6f}")


if __name__ == "__main__":
  main()
