from collections.abc import Callable
from dataclasses import dataclass
from types import NoneType


@dataclass(frozen=True)
class State[S, A]:
    run_state: Callable[[S], tuple[A, S]]

    def map[B](self, fn: Callable[[A], B]) -> State[S, B]:
        def _composed(s: S) -> tuple[B, S]:
            v = self.run_state(s)
            return fn(v[0]), v[1]

        return State(_composed)

    def map_state[Y](self, sy: Callable[[S], Y], ys: Callable[[Y], S]) -> State[Y, A]:
        def _inner(y: Y) -> tuple[A, Y]:
            s = ys(y)
            a, s1 = self.run_state(s)
            return a, sy(s1)

        return State(_inner)

    def bind[B](self, fn: Callable[[A], State[S, B]]) -> State[S, B]:
        def _inner(s: S) -> tuple[B, S]:
            a, s1 = self.run_state(s)
            return fn(a).run_state(s1)

        return State(_inner)


def pure[A, S = NoneType](v: A) -> State[S, A]:
    return State(lambda s: (v, s))


def lift[A, B, C, S](fn: Callable[[A, B], C]) -> Callable[[State[S, A], State[S, B]], State[S, C]]:
    def _inner(a: State[S, A], b: State[S, B]) -> State[S, C]:
        def _run_state(s: S) -> tuple[C, S]:
            v1, s1 = a.run_state(s)
            v2, s2 = b.run_state(s1)
            return fn(v1, v2), s2

        return State(_run_state)

    return _inner
