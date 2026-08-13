package io.brissach.probuild.structure;

import java.util.List;

public record Structure(int width, int height, int depth, List<BlockPlacement> blocks) {

  public int blockCount() {
    return blocks.size();
  }
}
