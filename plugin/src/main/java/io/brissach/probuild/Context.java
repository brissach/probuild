package io.brissach.probuild;

import org.bukkit.configuration.file.FileConfiguration;

public record Context(
  String backendUrl,
  String apiKey,
  String signingSecret,
  int timeoutMs,
  int maxWidth,
  int maxHeight,
  int maxDepth,
  int maxConcurrentGenerations,
  int maxBlocks,
  String placementBackend
) {

  public static Context from(FileConfiguration config) {
    return new Context(
      config.getString("backend.url", "http://localhost:8000"),
      config.getString("backend.api-key", ""),
      config.getString("backend.signing-secret", ""),
      config.getInt("backend.timeout-ms", 30000),
      config.getInt("generation.max-width", 32),
      config.getInt("generation.max-height", 32),
      config.getInt("generation.max-depth", 32),
      config.getInt("generation.max-concurrent-generations", 2),
      config.getInt("placement.max-blocks", 50000),
      config.getString("placement.backend", "auto")
    );
  }
}
