package io.brissach.probuild.world;

import com.sk89q.worldedit.MaxChangedBlocksException;
import com.sk89q.worldedit.WorldEdit;
import com.sk89q.worldedit.bukkit.BukkitAdapter;
import com.sk89q.worldedit.math.BlockVector3;
import com.sk89q.worldedit.world.block.BlockTypes;
import io.brissach.probuild.structure.Structure;
import io.brissach.probuild.util.Materials;
import org.bukkit.Location;

public final class WorldEditWorld implements AbstractWorld {

  @Override
  public int placeStructure(Location origin, Structure structure) {
    var bukkitWorld = origin.getWorld();
    if (bukkitWorld == null) {
      return 0;
    }
    var world = BukkitAdapter.adapt(bukkitWorld);
    var placed = 0;
    var baseX = origin.getBlockX();
    var baseY = origin.getBlockY();
    var baseZ = origin.getBlockZ();

    try (var session = WorldEdit.getInstance().newEditSession(world)) {
      for (var block : structure.blocks()) {
        var material = Materials.resolve(block.blockId());
        if (material.isAir()) {
          continue;
        }
        var blockType = BukkitAdapter.asBlockType(material);
        if (blockType == null) {
          continue;
        }
        var position = BlockVector3.at(
          baseX + block.x(),
          baseY + block.y(),
          baseZ + block.z()
        );
        try {
          session.setBlock(position, blockType.getDefaultState());
          placed++;
        } catch (MaxChangedBlocksException ex) {
          break;
        }
      }
    }

    return placed;
  }

  @Override
  public String id() {
    return "worldedit";
  }
}
