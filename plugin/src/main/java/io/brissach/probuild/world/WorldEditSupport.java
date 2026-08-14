package io.brissach.probuild.world;

import java.util.Locale;
import org.bukkit.Bukkit;
import org.bukkit.plugin.java.JavaPlugin;

public final class WorldEditSupport {

  private WorldEditSupport() {}

  public static boolean isPresent() {
    return Bukkit.getPluginManager().getPlugin("WorldEdit") != null;
  }

  public static AbstractWorld resolve(JavaPlugin plugin, String backend) {
    return switch (backend.toLowerCase(Locale.ROOT)) {
      case "paper" -> new PaperWorld();
      case "worldedit" -> worldEditOrFallback(plugin);
      default -> auto(plugin);
    };
  }

  private static AbstractWorld auto(JavaPlugin plugin) {
    if (isPresent()) {
      plugin.getLogger().info("WorldEdit detected, using EditSession placement");
      return new WorldEditWorld();
    }
    return new PaperWorld();
  }

  private static AbstractWorld worldEditOrFallback(JavaPlugin plugin) {
    if (!isPresent()) {
      plugin.getLogger().warning("placement.backend=worldedit but WorldEdit is not installed");
      return new PaperWorld();
    }
    return new WorldEditWorld();
  }
}
