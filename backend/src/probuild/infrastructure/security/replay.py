import time
from collections import OrderedDict
from threading import Lock


class ReplayGuard:
  def __init__(self, *, max_entries: int = 10_000, ttl_seconds: int = 600) -> None:
    self._max_entries = max_entries
    self._ttl_seconds = ttl_seconds
    self._seen: OrderedDict[str, float] = OrderedDict()
    self._lock = Lock()

  def _evict(self, now: float) -> None:
    expired = [key for key, ts in self._seen.items() if now - ts > self._ttl_seconds]
    for key in expired:
      self._seen.pop(key, None)
    while len(self._seen) > self._max_entries:
      self._seen.popitem(last=False)

  def check_and_record(self, request_id: str) -> bool:
    now = time.time()
    with self._lock:
      self._evict(now)
      if request_id in self._seen:
        return False
      self._seen[request_id] = now
      return True
