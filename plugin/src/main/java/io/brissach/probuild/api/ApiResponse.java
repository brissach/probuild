package io.brissach.probuild.api;

import io.brissach.probuild.structure.Structure;

public record ApiResponse(
  String generationId,
  Structure structure,
  long durationMs
) {}
