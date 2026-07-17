from collections.abc import Callable
from unittest.mock import Mock

import pytest

from fnkit.option import Just, Nothing, Option
from fnkit.result import Err, Ok, Result
from fnkit.state import State
from fnkit.transformers import o_bindt, r_bindt

state_just: State[int, Option[int]] = State(lambda s: (Just(5 + s), s + 0))
state_nothing: State[int, Option[int]] = State(lambda s: (Nothing(), s + 0))
state_just_mut: State[int, Option[int]] = State(lambda s: (Just(5 + s), s * 5))


def fn_just(v: int) -> State[int, Option[int]]:
    return State(lambda s: (Just(s + v), s))


def fn_nothing(_) -> State[int, Option[int]]:
    return State(lambda s: (Nothing(), s))


@pytest.mark.parametrize(
    ("inp", "state", "fn", "expected"),
    [
        (1, state_just, fn_just, (Just(7), 1)),
        (1, state_just_mut, fn_just, (Just(11), 5)),
        (1, state_just, fn_nothing, (Nothing(), 1)),
        (1, state_nothing, fn_just, (Nothing(), 1)),
        (1, state_nothing, fn_nothing, (Nothing(), 1)),
    ],
)
def test_o_bindt[A, B](
    inp: int,
    state: State[int, Option[A]],
    fn: Callable[[A], State[int, Option[B]]],
    expected: tuple[Option[B], int],
):
    assert o_bindt(state, fn).run_state(inp) == expected


state_ok: State[int, Result[int, str]] = State(lambda s: (Ok(s * 2), s + 0))
state_ok_mut: State[int, Result[int, str]] = State(lambda s: (Ok(s * 2), s << 3))
state_err: State[int, Result[int, str]] = State(lambda s: (Err("message"), s + 0))


def fn_ok(v: int) -> State[int, Result[int, str]]:
    return State(lambda s: (Ok(s + v), s + 0))


def fn_err(_) -> State[int, Result[int, str]]:
    return State(lambda s: (Err("error"), s + 0))


@pytest.mark.parametrize(
    ("inp", "state", "fn", "expected"),
    [
        (1, state_ok, fn_ok, (Ok(3), 1)),
        (1, state_ok_mut, fn_ok, (Ok(10), 8)),
        (1, state_ok, fn_err, (Err("error"), 1)),
        (1, state_err, fn_ok, (Err("message"), 1)),
        (1, state_err, fn_err, (Err("message"), 1)),
    ],
)
def test_r_bindt[A, B, E](
    inp: int,
    state: State[int, Result[A, E]],
    fn: Callable[[A], State[int, Result[B, E]]],
    expected: tuple[Result[B, E], int],
):
    assert r_bindt(state, fn).run_state(inp) == expected


def test_o_bindt_side_effects():
    mock = Mock()
    o_bindt(state_nothing, mock).run_state(42)
    assert mock.call_count == 0


def test_r_bindt_side_effects():
    mock = Mock()
    r_bindt(state_err, mock).run_state(42)
    assert mock.call_count == 0


def test_o_bindt_composability():
    def fn_a(v: int) -> State[int, Option[int]]:
        return State(lambda s: (Just(v + 1), s + 2))

    def fn_b(v: int) -> State[int, Option[int]]:
        return State(lambda s: (Just(v - 2), s + 3))

    first = o_bindt(o_bindt(state_just, fn_a), fn_b)
    second = o_bindt(o_bindt(state_just, fn_b), fn_a)

    assert first.run_state(1) == second.run_state(1)


def test_r_bindt_composability():
    def fn_a(v: int) -> State[int, Result[int, str]]:
        return State(lambda s: (Ok(v + 1), s + 2))

    def fn_b(v: int) -> State[int, Result[int, str]]:
        return State(lambda s: (Ok(v - 2), s + 3))

    first = r_bindt(r_bindt(state_ok, fn_a), fn_b)
    second = r_bindt(r_bindt(state_ok, fn_b), fn_a)

    assert first.run_state(1) == second.run_state(1)
