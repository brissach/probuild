package io.brissach.probuild.generation;

import org.bukkit.Location;

public record GenerationRequest(
  String prompt,
  Location origin,
  int width,
  int height,
  int depth,
  long seed
) {}
