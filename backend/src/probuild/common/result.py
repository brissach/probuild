from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")
E = TypeVar("E")


@dataclass(frozen=True, slots=True)
class Ok(Generic[T]):
  value: T


@dataclass(frozen=True, slots=True)
class Err(Generic[E]):
  error: E


Result = Ok[T] | Err[E]


def is_ok(result: Result[T, E]) -> bool:
  return isinstance(result, Ok)


def unwrap(result: Result[T, E]) -> T:
  if isinstance(result, Ok):
    return result.value
  raise ValueError(f"attempted to unwrap Err: {result.error}")
