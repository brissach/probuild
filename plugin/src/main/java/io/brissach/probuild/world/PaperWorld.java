package io.brissach.probuild.world;

import io.brissach.probuild.structure.Structure;
import io.brissach.probuild.util.Materials;
import org.bukkit.Location;

public final class PaperWorld implements AbstractWorld {

  @Override
  public int placeStructure(Location origin, Structure structure) {
    var world = origin.getWorld();
    if (world == null) {
      return 0;
    }
    var placed = 0;
    var baseX = origin.getBlockX();
    var baseY = origin.getBlockY();
    var baseZ = origin.getBlockZ();
    for (var block : structure.blocks()) {
      var material = Materials.resolve(block.blockId());
      if (material.isAir()) {
        continue;
      }
      world.getBlockAt(baseX + block.x(), baseY + block.y(), baseZ + block.z())
        .setType(material, false);
      placed++;
    }
    return placed;
  }

  @Override
  public String id() {
    return "paper";
  }
}
