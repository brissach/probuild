import argparse
from pathlib import Path

from probuild.ml.models.voxel_autoencoder import VoxelAutoencoder
from probuild.ml.training.datasets import load_npz_dataset
from probuild.ml.training.trainer import Trainer, TrainingConfig


def main() -> None:
  parser = argparse.ArgumentParser(description="Train Probuild models")
  parser.add_argument("--data", type=Path, required=True)
  parser.add_argument("--epochs", type=int, default=10)
  parser.add_argument("--batch-size", type=int, default=4)
  parser.add_argument("--device", default="cpu")
  parser.add_argument("--checkpoint-dir", type=Path, default=Path("artifacts/checkpoints"))
  args = parser.parse_args()

  dataset = load_npz_dataset(args.data)
  model = VoxelAutoencoder(num_blocks=16, input_size=(32, 32, 32)).to(args.device)
  trainer = Trainer(
    model=model,
    config=TrainingConfig(
      epochs=args.epochs,
      batch_size=args.batch_size,
      checkpoint_dir=args.checkpoint_dir,
      device=args.device,
    ),
    dataset=dataset,
  )
  trainer.run()


if __name__ == "__main__":
  main()
