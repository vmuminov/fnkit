from collections.abc import Callable, Iterable
from functools import partial
from operator import add, mul
from typing import Any
from unittest.mock import Mock

import pytest

from fnkit.collection import Collection, lift, pure, sequence
from fnkit.option import Just, Nothing
from fnkit.result import Err, Ok
from fnkit.state import State


def test_pure():
    pured = pure(2)
    assert isinstance(pured, Collection)
    assert list(pured) == [2]


@pytest.mark.parametrize(
    ("inp", "fn", "exp"),
    [
        ((), str, []),
        ((1, 2, 3), str, ["1", "2", "3"]),
        (("a", "b", "c"), lambda x: x * 2, ["aa", "bb", "cc"]),
    ],
)
def test_map[T, U](inp: Iterable[T], fn: Callable[[T], U], exp: list[U]):
    actual = list(Collection(inp).map(fn))
    assert actual == exp


@pytest.mark.parametrize(
    ("inp", "fn", "exp"),
    [
        ([], lambda x: [x, -x], []),
        ([1, 2, 3], lambda x: [x, -x], [1, -1, 2, -2, 3, -3]),
        ([1, 2, 3], lambda _: [], []),
    ],
)
def test_bind[T, U](inp: Iterable[T], fn: Callable[[T], Collection[U]], exp: list[U]):
    actual = list(Collection(inp).bind(fn))
    assert actual == exp


@pytest.mark.parametrize(
    ("inp", "fn", "init", "exp"),
    [
        ([], add, 0, 0),
        ([1, 2, 3], add, 0, 6),
        (["a", "b", "c"], add, "", "abc"),
    ],
)
def test_reduce[T, U](inp: Iterable[T], fn: Callable[[U, T], U], init: U, exp: U):
    actual = Collection(inp).reduce(fn, init)
    assert actual == exp


@pytest.mark.parametrize(
    ("inp1", "inp2", "fn", "exp"),
    [
        ([], [1, 2, 3], mul, []),
        ([1, 2, 3], [], mul, []),
        ([1, 2, 3], [4, 5, 6], mul, [4, 5, 6, 8, 10, 12, 12, 15, 18]),
    ],
)
def test_lift[T, U, V](inp1: Iterable[T], inp2: Iterable[U], fn: Callable[[T, U], V], exp: list[V]):
    c1 = Collection(inp1)
    c2 = Collection(inp2)
    lifted = lift(fn)
    actual = list(lifted(c1, c2))
    assert actual == exp


@pytest.mark.parametrize(
    ("inp", "exp"),
    [
        ([], Collection([])),
        ([1, 2, 3], Collection([1, 2, 3])),
        ([Just(1), Just(2), Just(3)], Just(Collection([1, 2, 3]))),
        ([Just(1), Nothing(), Just(3)], Nothing()),
        ([Ok("a"), Ok("b"), Ok("c")], Ok(Collection(["a", "b", "c"]))),
        ([Ok("a"), Err("err 1"), Ok("b"), Err("err 2")], Err("err 1")),
    ],
)
def test_sequence[T](inp: Iterable[T], exp: Any):
    actual = sequence(Collection(inp))

    def assert_eq(left: Any, right: Any) -> None:
        match left:
            case Collection():
                for item_left, item_right in zip(left, right, strict=True):
                    assert item_left == item_right
            case _:
                assert left == right

    match actual:
        case Just() | Ok():
            assert_eq(actual.v, exp.v)
        case _:
            assert_eq(actual, exp)


def test_sequence_state():
    def state1(s: int) -> tuple[int, int]:
        return (s * 2, s + 1)

    def state2(s: int) -> tuple[int, int]:
        return (s + 5, s + 1)

    def state3(s: int) -> tuple[int, int]:
        return (s // 3, s + 1)

    states = map(State, (state1, state2, state3))
    collection = Collection(states)
    actual, final_state = sequence(collection).run_state(42)

    assert list(actual) == [84, 48, 14]
    assert final_state == 45


@pytest.mark.parametrize(
    "fn",
    [
        Collection([]).map,
        Collection([]).bind,
        partial(Collection([]).reduce, init=[]),
    ],
)
def test_side_effects(fn: Callable):
    mock = Mock()
    list(fn(mock))
    assert mock.call_count == 0


def test_iter_consumes():
    consumable = map(str, (1, 2, 3))
    collection = Collection(consumable)
    assert list(collection) == ["1", "2", "3"]
    assert list(collection) == []
