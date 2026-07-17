from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol


class Result[T, E](Protocol):
    def map[U](self, fn: Callable[[T], U]) -> Result[U, E]: ...
    def map_err[F](self, fn: Callable[[E], F]) -> Result[T, F]: ...
    def bind[U](self, fn: Callable[[T], Result[U, E]]) -> Result[U, E]: ...
    def ok_or(self, fn: Callable[[E], T]) -> T: ...


def pure[T, E = Exception](v: T) -> Result[T, E]:
    return Ok(v)


def lift[A, B, C, E](
    fn: Callable[[A, B], C],
) -> Callable[[Result[A, E], Result[B, E]], Result[C, E]]:
    def _inner(a: Result[A, E], b: Result[B, E]) -> Result[C, E]:
        return a.bind(lambda w: b.map(lambda v: fn(w, v)))

    return _inner


@dataclass(frozen=True, slots=True)
class Ok[T, E](Result[T, E]):
    v: T

    def map[U](self, fn: Callable[[T], U]) -> Result[U, E]:
        return Ok(fn(self.v))

    def map_err[F](self, fn: Callable[[E], F]) -> Result[T, F]:
        return self  # type: ignore

    def bind[U](self, fn: Callable[[T], Result[U, E]]) -> Result[U, E]:
        return fn(self.v)

    def ok_or(self, fn: Callable[[E], T]) -> T:
        return self.v


@dataclass(frozen=True, slots=True)
class Err[T, E](Result[T, E]):
    v: E

    def map[U](self, fn: Callable[[T], U]) -> Result[U, E]:
        return self  # type: ignore

    def bind[U](self, fn: Callable[[T], Result[U, E]]) -> Result[U, E]:
        return self  # type: ignore

    def ok_or(self, fn: Callable[[E], T]) -> T:
        return fn(self.v)

    def map_err[F](self, fn: Callable[[E], F]) -> Result[T, F]:
        return Err(fn(self.v))
