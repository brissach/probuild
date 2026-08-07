import time
from collections import defaultdict
from threading import Lock


class RateLimiter:
  def __init__(self, *, limit_per_minute: int) -> None:
    self._limit = limit_per_minute
    self._windows: dict[str, list[float]] = defaultdict(list)
    self._lock = Lock()

  def allow(self, key: str) -> bool:
    now = time.time()
    window_start = now - 60.0
    with self._lock:
      timestamps = [ts for ts in self._windows[key] if ts >= window_start]
      if len(timestamps) >= self._limit:
        self._windows[key] = timestamps
        return False
      timestamps.append(now)
      self._windows[key] = timestamps
      return True
