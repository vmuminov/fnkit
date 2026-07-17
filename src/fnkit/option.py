from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol


class Option[T](Protocol):
    def map[U](self, fn: Callable[[T], U]) -> Option[U]: ...
    def bind[U](self, fn: Callable[[T], Option[U]]) -> Option[U]: ...
    def just_or(self, fn: Callable[[], T]) -> T: ...


def pure[T](v: T) -> Option[T]:
    return Just(v)


def lift[A, B, C](fn: Callable[[A, B], C]) -> Callable[[Option[A], Option[B]], Option[C]]:
    def _inner(a: Option[A], b: Option[B]) -> Option[C]:
        return a.bind(lambda w: b.map(lambda v: fn(w, v)))

    return _inner


@dataclass(frozen=True, slots=True)
class Just[T](Option[T]):
    v: T

    def map[U](self, fn: Callable[[T], U]) -> Just[U]:
        return Just(fn(self.v))

    def bind[U](self, fn: Callable[[T], Option[U]]) -> Option[U]:
        return fn(self.v)

    def just_or(self, fn: Callable[[], T]) -> T:
        return self.v


class Nothing[T](Option[T]):
    def map[U](self, fn: Callable[[T], U]) -> Option[U]:
        return self  # type: ignore

    def bind[U](self, fn: Callable[[T], Option[U]]) -> Option[U]:
        return self  # type: ignore

    def just_or(self, fn: Callable[[], T]) -> T:
        return fn()

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Nothing)

    def __hash__(self) -> int:
        return hash(Nothing)

    def __repr__(self) -> str:
        return "Nothing()"
