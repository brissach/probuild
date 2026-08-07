from prometheus_client import Counter, Histogram

GENERATION_COUNT = Counter(
  "probuild_generation_total",
  "Total generation requests",
  ["status"],
)
GENERATION_DURATION = Histogram(
  "probuild_generation_duration_seconds",
  "Generation duration in seconds",
  buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0),
)
MODEL_LOAD_TIME = Histogram(
  "probuild_model_load_seconds",
  "Model load duration in seconds",
)
VALIDATION_FAILURES = Counter(
  "probuild_validation_failures_total",
  "Structure validation failures",
)
CACHE_HITS = Counter("probuild_cache_hits_total", "Cache hits")
CACHE_MISSES = Counter("probuild_cache_misses_total", "Cache misses")
