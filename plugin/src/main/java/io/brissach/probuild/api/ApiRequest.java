package io.brissach.probuild.api;

public record ApiRequest(
  String prompt,
  long seed,
  int width,
  int height,
  int depth,
  double temperature,
  int topK
) {}
