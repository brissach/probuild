package io.brissach.probuild.util;

import java.util.Map;
import org.bukkit.Material;

public final class Materials {

  private static final Map<String, Material> REGISTRY = Map.ofEntries(
    Map.entry("air", Material.AIR),
    Map.entry("stone", Material.STONE),
    Map.entry("cobblestone", Material.COBBLESTONE),
    Map.entry("stone_bricks", Material.STONE_BRICKS),
    Map.entry("oak_planks", Material.OAK_PLANKS),
    Map.entry("oak_log", Material.OAK_LOG),
    Map.entry("oak_leaves", Material.OAK_LEAVES),
    Map.entry("glass", Material.GLASS),
    Map.entry("bricks", Material.BRICKS),
    Map.entry("dirt", Material.DIRT),
    Map.entry("grass_block", Material.GRASS_BLOCK),
    Map.entry("sand", Material.SAND),
    Map.entry("spruce_planks", Material.SPRUCE_PLANKS),
    Map.entry("spruce_log", Material.SPRUCE_LOG),
    Map.entry("water", Material.WATER),
    Map.entry("torch", Material.TORCH)
  );

  private Materials() {}

  public static boolean isSupported(String blockId) {
    return REGISTRY.containsKey(blockId);
  }

  public static Material resolve(String blockId) {
    return REGISTRY.getOrDefault(blockId, Material.AIR);
  }
}
