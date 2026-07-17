from collections.abc import Callable

from fnkit.option import Just, Option
from fnkit.result import Ok, Result
from fnkit.state import State


def r_bindt[S, A, B, E](
    state: State[S, Result[A, E]],
    fn: Callable[[A], State[S, Result[B, E]]],
) -> State[S, Result[B, E]]:
    """
    r_bindt :: State s (Result a e) ->
               (a -> State s (Result b e)) ->
               State s (Result b e)
    """

    def _inner(s: S) -> tuple[Result[B, E], S]:
        result, s1 = state.run_state(s)
        match result:
            case Ok(value):
                return fn(value).run_state(s1)
            case _:
                return result, s1  # type: ignore

    return State(_inner)


def o_bindt[S, A, B](
    state: State[S, Option[A]],
    fn: Callable[[A], State[S, Option[B]]],
) -> State[S, Option[B]]:
    """
    o_bindt :: State s (Option a) ->
               (a -> State s (Option b)) ->
               State s (Option b)
    """

    def _inner(s: S) -> tuple[Option[B], S]:
        result, s1 = state.run_state(s)
        match result:
            case Just(value):
                return fn(value).run_state(s1)
            case _:
                return result, s1  # type: ignore

    return State(_inner)
