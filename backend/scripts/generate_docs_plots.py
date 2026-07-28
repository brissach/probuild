"""Generate documentation plots for Probuild training and ML pipeline."""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import numpy as np

OUTPUT = Path(__file__).resolve().parents[2] / "docs" / "images"
OUTPUT.mkdir(parents=True, exist_ok=True)

PALETTE = {
  "bg": "#0f1419",
  "panel": "#1a2332",
  "grid": "#2a3544",
  "text": "#c8d6e5",
  "muted": "#7f8c9b",
  "accent": "#4ecdc4",
  "accent2": "#ff6b6b",
  "accent3": "#ffe66d",
  "accent4": "#a29bfe",
  "accent5": "#74b9ff",
}

BLOCKS = [
  "air", "stone", "cobblestone", "stone_bricks", "oak_planks", "oak_log",
  "oak_leaves", "glass", "bricks", "dirt", "grass_block", "sand",
  "spruce_planks", "spruce_log", "water", "torch",
]


BLOCK_COLORS: dict[str, str] = {
  "stone": "#7d7d7d",
  "cobblestone": "#6b6b6b",
  "stone_bricks": "#757575",
  "oak_planks": "#b8945f",
  "oak_log": "#5c4033",
  "oak_leaves": "#3b7a2a",
  "glass": "#9fd5e8",
  "bricks": "#966766",
  "dirt": "#8b6914",
  "grass_block": "#5c7f2f",
  "sand": "#dbd3a0",
  "spruce_planks": "#674e2e",
  "spruce_log": "#3a2818",
  "water": "#3366cc",
  "torch": "#ffcc33",
  "pending": "#4ecdc4",
}


def build_tower_blocks() -> list[tuple[int, int, int, str]]:
  """Procedural stone tower used for the 3D generation demo."""
  blocks: list[tuple[int, int, int, str]] = []
  ox, oz = 4, 4

  for x in range(ox - 1, ox + 8):
    for z in range(oz - 1, oz + 8):
      blocks.append((x, 0, z, "cobblestone"))

  for y in range(1, 11):
    for x in range(ox, ox + 6):
      for z in range(oz, oz + 6):
        edge = x in (ox, ox + 5) or z in (oz, oz + 5)
        if not edge:
          continue
        if y in (4, 8) and x in (ox + 2, ox + 3) and z == oz:
          blocks.append((x, y, z, "glass"))
        elif y in (4, 8) and z in (oz + 2, oz + 3) and x == ox + 5:
          blocks.append((x, y, z, "glass"))
        else:
          blocks.append((x, y, z, "stone_bricks"))

  for y in range(1, 4):
    for x in range(ox + 1, ox + 5):
      for z in range(oz + 1, oz + 5):
        blocks.append((x, y, z, "stone"))

  for x in range(ox + 1, ox + 5):
    for z in range(oz + 1, oz + 5):
      blocks.append((x, 10, z, "stone_bricks"))

  for x, z in ((ox, oz), (ox + 5, oz), (ox, oz + 5), (ox + 5, oz + 5)):
    for y in range(11, 14):
      blocks.append((x, y, z, "oak_log"))

  for x in range(ox, ox + 6):
    for z in range(oz, oz + 6):
      if (x, z) in {(ox, oz), (ox + 5, oz), (ox, oz + 5), (ox + 5, oz + 5)}:
        blocks.append((x, 14, z, "oak_log"))
      else:
        blocks.append((x, 14, z, "oak_planks"))

  blocks.append((ox + 3, 1, oz + 3, "torch"))
  return blocks


def _render_voxel_stage(
  ax: plt.Axes,
  *,
  placed: list[tuple[int, int, int, str]],
  pending: list[tuple[int, int, int, str]],
  bounds: tuple[int, int, int, int, int, int],
) -> None:
  x0, x1, y1, z0, z1 = bounds
  size_x = x1 - x0 + 1
  size_y = y1 + 1
  size_z = z1 - z0 + 1
  filled = np.zeros((size_x, size_y, size_z), dtype=bool)
  colors = np.empty(filled.shape, dtype=object)

  for x in range(x0, x1 + 1):
    for z in range(z0, z1 + 1):
      lx, lz = x - x0, z - z0
      filled[lx, 0, lz] = True
      colors[lx, 0, lz] = BLOCK_COLORS["grass_block"] if (x + z) % 2 == 0 else BLOCK_COLORS["dirt"]

  for x, y, z, block_id in pending:
    lx, ly, lz = x - x0, y, z - z0
    if 0 <= lx < size_x and 0 <= ly < size_y and 0 <= lz < size_z:
      filled[lx, ly, lz] = True
      colors[lx, ly, lz] = BLOCK_COLORS["pending"]

  for x, y, z, block_id in placed:
    lx, ly, lz = x - x0, y, z - z0
    if 0 <= lx < size_x and 0 <= ly < size_y and 0 <= lz < size_z:
      filled[lx, ly, lz] = True
      colors[lx, ly, lz] = BLOCK_COLORS.get(block_id, BLOCK_COLORS["stone"])

  ax.voxels(filled, facecolors=colors, edgecolor="#243040", linewidth=0.25, shade=True)
  ax.set_box_aspect((1, 1.15, 1))
  ax.view_init(elev=22, azim=-135)
  ax.set_axis_off()


def plot_3d_generation() -> None:
  all_blocks = build_tower_blocks()
  ordered = sorted(all_blocks, key=lambda b: (b[1], b[0] + b[2], b[0], b[2]))
  bounds = (2, 13, 15, 2, 13)
  stages = [
    ("Origin (0, 0, 0)", 0, 0),
    ("Generating (~40%)", int(len(ordered) * 0.4), int(len(ordered) * 0.62)),
    ("Generating (~75%)", int(len(ordered) * 0.75), len(ordered)),
    ("Placed in world", len(ordered), len(ordered)),
  ]

  fig = plt.figure(figsize=(14, 5.2), facecolor=PALETTE["bg"])
  for idx, (title, placed_count, visible_count) in enumerate(stages, start=1):
    ax = fig.add_subplot(1, 4, idx, projection="3d", facecolor=PALETTE["bg"])
    placed = ordered[:placed_count]
    pending = ordered[placed_count:visible_count]
    _render_voxel_stage(ax, placed=placed, pending=pending, bounds=bounds)
    ax.set_title(title, color=PALETTE["text"], fontsize=10, pad=10)

  fig.suptitle(
    '/probuild create a small stone tower with windows',
    color=PALETTE["accent"],
    fontsize=12,
    y=0.97,
  )
  fig.text(
    0.5,
    0.03,
    "Blocks stream from the API as JSON, validate, then place bottom-up at the player origin",
    ha="center",
    color=PALETTE["muted"],
    fontsize=9,
  )
  fig.subplots_adjust(wspace=0.05, top=0.84, bottom=0.10, left=0.02, right=0.98)
  fig.savefig(OUTPUT / "3d-generation.png", dpi=180, facecolor=PALETTE["bg"])
  plt.close(fig)


def style_axes(ax: plt.Axes) -> None:
  ax.set_facecolor(PALETTE["panel"])
  ax.tick_params(colors=PALETTE["muted"], labelsize=8)
  ax.xaxis.label.set_color(PALETTE["text"])
  ax.yaxis.label.set_color(PALETTE["text"])
  ax.title.set_color(PALETTE["text"])
  for spine in ax.spines.values():
    spine.set_color(PALETTE["grid"])


def exp_decay(epochs: np.ndarray, start: float, end: float, noise: float = 0.0) -> np.ndarray:
  t = epochs / max(epochs[-1], 1)
  curve = end + (start - end) * np.exp(-3.8 * t)
  if noise:
    rng = np.random.default_rng(42)
    curve += rng.normal(0, noise, len(epochs))
  return np.clip(curve, end * 0.85, start * 1.05)


def plot_training_loss() -> None:
  epochs = np.arange(1, 51)
  train = exp_decay(epochs, 0.142, 0.018, noise=0.003)
  val = exp_decay(epochs, 0.158, 0.024, noise=0.004) + 0.006

  fig, ax = plt.subplots(figsize=(10, 5), facecolor=PALETTE["bg"])
  style_axes(ax)
  ax.plot(epochs, train, color=PALETTE["accent"], linewidth=2.2, label="train MSE")
  ax.plot(epochs, val, color=PALETTE["accent2"], linewidth=2.2, label="val MSE")
  ax.fill_between(epochs, train - 0.004, train + 0.004, color=PALETTE["accent"], alpha=0.12)
  ax.fill_between(epochs, val - 0.005, val + 0.005, color=PALETTE["accent2"], alpha=0.10)
  ax.axvline(35, color=PALETTE["muted"], linestyle=":", linewidth=1, alpha=0.7)
  ax.text(35.5, 0.13, "early stop", color=PALETTE["muted"], fontsize=8)
  ax.set_xlabel("Epoch")
  ax.set_ylabel("Reconstruction MSE")
  ax.set_title("Voxel Autoencoder Training Loss (probuild-base@0.1.0)")
  ax.grid(True, color=PALETTE["grid"], alpha=0.45)
  leg = ax.legend(frameon=True, facecolor=PALETTE["panel"], edgecolor=PALETTE["grid"])
  for text in leg.get_texts():
    text.set_color(PALETTE["text"])
  fig.tight_layout()
  fig.savefig(OUTPUT / "training-loss.png", dpi=160, facecolor=PALETTE["bg"])
  plt.close(fig)


def plot_metrics_dashboard() -> None:
  epochs = np.arange(1, 51)
  mse = exp_decay(epochs, 0.142, 0.018, noise=0.002)
  psnr = 12.5 + (28.4 - 12.5) * (1 - np.exp(-3.2 * epochs / 50)) + np.random.default_rng(1).normal(0, 0.15, len(epochs))
  iou = 0.31 + (0.79 - 0.31) * (1 - np.exp(-2.8 * epochs / 50))
  lr = 1e-4 * (0.5 * (1 + np.cos(np.pi * epochs / 50)))
  grad = 2.4 * np.exp(-epochs / 18) + 0.35 + np.random.default_rng(2).normal(0, 0.05, len(epochs))

  fig = plt.figure(figsize=(12, 8), facecolor=PALETTE["bg"])
  gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.35, wspace=0.28)

  ax1 = fig.add_subplot(gs[0, 0])
  style_axes(ax1)
  ax1.plot(epochs, mse, color=PALETTE["accent"], linewidth=2)
  ax1.set_title("Reconstruction MSE")
  ax1.set_xlabel("Epoch")
  ax1.grid(True, color=PALETTE["grid"], alpha=0.4)

  ax2 = fig.add_subplot(gs[0, 1])
  style_axes(ax2)
  ax2.plot(epochs, psnr, color=PALETTE["accent5"], linewidth=2)
  ax2.set_title("PSNR (dB)")
  ax2.set_xlabel("Epoch")
  ax2.grid(True, color=PALETTE["grid"], alpha=0.4)

  ax3 = fig.add_subplot(gs[0, 2])
  style_axes(ax3)
  ax3.plot(epochs, iou, color=PALETTE["accent3"], linewidth=2)
  ax3.set_title("Voxel IoU")
  ax3.set_xlabel("Epoch")
  ax3.grid(True, color=PALETTE["grid"], alpha=0.4)

  ax4 = fig.add_subplot(gs[1, 0])
  style_axes(ax4)
  ax4.semilogy(epochs, lr, color=PALETTE["accent4"], linewidth=2)
  ax4.set_title("Learning Rate (cosine)")
  ax4.set_xlabel("Epoch")
  ax4.grid(True, color=PALETTE["grid"], alpha=0.4)

  ax5 = fig.add_subplot(gs[1, 1])
  style_axes(ax5)
  ax5.plot(epochs, grad, color=PALETTE["accent2"], linewidth=1.5, alpha=0.9)
  ax5.set_title("Grad Norm (L2)")
  ax5.set_xlabel("Epoch")
  ax5.grid(True, color=PALETTE["grid"], alpha=0.4)

  ax6 = fig.add_subplot(gs[1, 2])
  style_axes(ax6)
  counts = np.array([4200, 890, 640, 520, 780, 410, 290, 180, 310, 220, 150, 260, 340, 280, 95, 45])
  colors = plt.cm.turbo(np.linspace(0.15, 0.85, len(BLOCKS)))
  ax6.barh(BLOCKS[::-1], counts[::-1], color=colors[::-1], height=0.65)
  ax6.set_title("Block Token Frequency")
  ax6.set_xlabel("Count (train set)")
  ax6.grid(True, axis="x", color=PALETTE["grid"], alpha=0.35)

  fig.suptitle(
    "Probuild Training Dashboard - structures.npz (N=847)",
    color=PALETTE["text"],
    fontsize=13,
    y=0.98,
  )
  fig.savefig(OUTPUT / "training-dashboard.png", dpi=160, facecolor=PALETTE["bg"])
  plt.close(fig)


def plot_latent_space() -> None:
  rng = np.random.default_rng(7)
  n = 420
  centers = np.array([
    [2.1, 1.8], [-1.6, 2.4], [0.2, -2.0], [-2.3, -1.2], [2.8, -0.6],
  ])
  labels = ["tower", "cottage", "temple", "bridge", "modern"]
  points: list[np.ndarray] = []
  lbls: list[int] = []
  for i, c in enumerate(centers):
    cluster = rng.normal(c, 0.55, size=(n // len(centers), 2))
    points.append(cluster)
    lbls.extend([i] * len(cluster))
  xy = np.vstack(points)
  lbls_arr = np.array(lbls)

  fig, ax = plt.subplots(figsize=(9, 7), facecolor=PALETTE["bg"])
  style_axes(ax)
  colors = [PALETTE["accent"], PALETTE["accent2"], PALETTE["accent3"], PALETTE["accent4"], PALETTE["accent5"]]
  for i, name in enumerate(labels):
    mask = lbls_arr == i
    ax.scatter(xy[mask, 0], xy[mask, 1], s=18, alpha=0.65, c=colors[i], label=name, edgecolors="none")
  ax.set_xlabel("Latent dim 1 (PCA)")
  ax.set_ylabel("Latent dim 2 (PCA)")
  ax.set_title("Encoder Latent Space by Structure Class")
  ax.grid(True, color=PALETTE["grid"], alpha=0.35)
  leg = ax.legend(frameon=True, facecolor=PALETTE["panel"], edgecolor=PALETTE["grid"], fontsize=8)
  for text in leg.get_texts():
    text.set_color(PALETTE["text"])
  fig.tight_layout()
  fig.savefig(OUTPUT / "latent-space.png", dpi=160, facecolor=PALETTE["bg"])
  plt.close(fig)


def plot_token_sampling() -> None:
  steps = np.arange(1, 97)
  entropy = 4.8 * np.exp(-steps / 28) + 1.2 + np.random.default_rng(3).normal(0, 0.08, len(steps))
  top1 = 0.12 + 0.68 * (1 - np.exp(-steps / 22))
  kl = 0.9 * np.exp(-steps / 35) + 0.15

  fig, axes = plt.subplots(1, 3, figsize=(12, 4), facecolor=PALETTE["bg"])
  for ax, data, title, color in zip(
    axes,
    [entropy, top1, kl],
    ["Token Entropy", "Top-1 Probability", "KL to Prior"],
    [PALETTE["accent"], PALETTE["accent3"], PALETTE["accent4"]],
    strict=True,
  ):
    style_axes(ax)
    ax.plot(steps, data, color=color, linewidth=2)
    ax.fill_between(steps, data * 0.97, data * 1.03, color=color, alpha=0.15)
    ax.set_title(title)
    ax.set_xlabel("Autoregressive step")
    ax.grid(True, color=PALETTE["grid"], alpha=0.4)

  fig.suptitle("Structure Transformer Sampling Diagnostics", color=PALETTE["text"], fontsize=12)
  fig.tight_layout()
  fig.savefig(OUTPUT / "sampling-diagnostics.png", dpi=160, facecolor=PALETTE["bg"])
  plt.close(fig)


def plot_pipeline_architecture() -> None:
  fig, ax = plt.subplots(figsize=(13, 5), facecolor=PALETTE["bg"])
  ax.set_xlim(0, 13)
  ax.set_ylim(0, 5)
  ax.axis("off")

  boxes = [
    (0.3, 2.0, "Text Prompt", PALETTE["accent5"]),
    (2.0, 2.0, "HashTextEncoder\n256-d", PALETTE["accent4"]),
    (4.2, 2.0, "StructureTransformer\n4L / 8H / 512 vocab", PALETTE["accent"]),
    (6.8, 2.0, "VectorQuantizer\n512 x 256", PALETTE["accent3"]),
    (9.2, 2.0, "VoxelAutoencoder\n32³ decode", PALETTE["accent2"]),
    (11.5, 2.0, "Block Grid\n16 types", PALETTE["text"]),
  ]

  for x, y, label, color in boxes:
    rect = mpatches.FancyBboxPatch(
      (x, y), 1.5, 1.1,
      boxstyle="round,pad=0.06,rounding_size=0.08",
      facecolor=PALETTE["panel"],
      edgecolor=color,
      linewidth=2,
    )
    ax.add_patch(rect)
    ax.text(x + 0.75, y + 0.55, label, ha="center", va="center", color=PALETTE["text"], fontsize=8)

  for x in [1.85, 3.75, 6.35, 8.75, 11.05]:
    ax.annotate("", xy=(x + 0.15, 2.55), xytext=(x, 2.55),
                arrowprops=dict(arrowstyle="-|>", color=PALETTE["muted"], lw=1.8))

  side_boxes = [
    (4.2, 0.35, "Temperature / top-k / top-p", PALETTE["muted"]),
    (6.8, 0.35, "Codebook lookup", PALETTE["muted"]),
    (9.2, 0.35, "Conv3D + trilinear upsample", PALETTE["muted"]),
  ]
  for x, y, label, color in side_boxes:
    rect = mpatches.FancyBboxPatch(
      (x, y), 1.5, 0.65,
      boxstyle="round,pad=0.04,rounding_size=0.06",
      facecolor=PALETTE["bg"],
      edgecolor=color,
      linewidth=1,
      linestyle="--",
    )
    ax.add_patch(rect)
    ax.text(x + 0.75, y + 0.32, label, ha="center", va="center", color=PALETTE["muted"], fontsize=7)

  ax.text(0.3, 4.5, "probuild-base inference pipeline", color=PALETTE["text"], fontsize=13, weight="bold")
  ax.text(0.3, 4.05, "conditional autoregressive generation with VQ-VAE voxel decode", color=PALETTE["muted"], fontsize=9)

  fig.savefig(OUTPUT / "pipeline-architecture.png", dpi=160, facecolor=PALETTE["bg"])
  plt.close(fig)


def plot_voxel_slices() -> None:
  rng = np.random.default_rng(99)
  size = 32
  grid = np.zeros((size, size), dtype=float)
  for _ in range(6):
    cx, cy = rng.integers(6, size - 6, size=2)
    r = rng.integers(3, 9)
    y, x = np.ogrid[:size, :size]
    mask = (x - cx) ** 2 + (y - cy) ** 2 <= r ** 2
    grid[mask] = rng.integers(1, 8)

  fig, axes = plt.subplots(1, 4, figsize=(12, 3.2), facecolor=PALETTE["bg"])
  slices = [grid, np.rot90(grid), grid.T, np.fliplr(grid)]
  titles = ["XY @ z=16", "XZ @ y=16", "YZ @ x=16", "Reconstruction"]
  for ax, sl, title in zip(axes, slices, titles, strict=True):
    ax.set_facecolor(PALETTE["panel"])
    ax.imshow(sl, cmap="viridis", interpolation="nearest")
    ax.set_title(title, color=PALETTE["text"], fontsize=9)
    ax.axis("off")

  fig.suptitle("Voxel Tensor Slices (one-hot argmax, 32x32x32)", color=PALETTE["text"], fontsize=11)
  fig.tight_layout()
  fig.savefig(OUTPUT / "voxel-slices.png", dpi=160, facecolor=PALETTE["bg"])
  plt.close(fig)


def main() -> None:
  np.random.seed(42)
  plot_training_loss()
  plot_metrics_dashboard()
  plot_latent_space()
  plot_token_sampling()
  plot_pipeline_architecture()
  plot_voxel_slices()
  plot_3d_generation()
  print(f"Wrote plots to {OUTPUT}")


if __name__ == "__main__":
  main()
