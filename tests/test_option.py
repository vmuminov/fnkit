from collections.abc import Callable
from operator import add
from unittest.mock import Mock

import pytest

from fnkit.option import Just, Nothing, Option, lift, pure


def test_pure():
    pured = pure(5)
    assert isinstance(pured, Just)
    assert pured.v == 5


@pytest.mark.parametrize(
    ("option", "fn", "u"),
    [
        (Just(5), str, Just("5")),
        (Nothing(), str, Nothing()),
        (Just([1, 2, 3]), lambda seq: len(seq) > 0, Just(True)),
    ],
)
def test_map[T, U](option: Option[T], fn: Callable[[T], U], u: Option[U]):
    assert option.map(fn) == u


@pytest.mark.parametrize(
    ("option", "fn", "u"),
    [
        (Just(1), lambda inp: Just(inp + 3), Just(4)),
        (Just(2), lambda _: Nothing(), Nothing()),
        (Nothing(), lambda _: Just("hello"), Nothing()),
        (Nothing(), lambda _: Nothing(), Nothing()),
    ],
)
def test_bind[T, U](option: Option[T], fn: Callable[[T], Option[U]], u: Option[U]):
    assert option.bind(fn) == u


@pytest.mark.parametrize(
    ("option", "fn", "t"),
    [
        (Just(42), lambda: 67, 42),
        (Nothing(), lambda: 11, 11),
    ],
)
def test_just_or[T](option: Option[T], fn: Callable[[], T], t: T):
    assert option.just_or(fn) == t


@pytest.mark.parametrize(
    ("fn", "first", "second", "result"),
    [
        (add, Just("abc"), Just("cde"), Just("abccde")),
        (add, Just("abc"), Nothing(), Nothing()),
        (add, Nothing(), Just("abc"), Nothing()),
        (add, Nothing(), Nothing(), Nothing()),
    ],
)
def test_lift[A, B, C](
    fn: Callable[[A, B], C], first: Option[A], second: Option[B], result: Option[C]
):
    assert lift(fn)(first, second) == result


def test_eq():
    assert Just(1) == Just(1)
    assert Just(1) != Just(2)
    assert Nothing() == Nothing()


def test_hash():
    assert hash(Nothing()) == hash(Nothing())
    assert hash(Just(2)) == hash(Just(2))
    assert hash(Just(2)) != hash(Just(4))


@pytest.mark.parametrize(("option", "expected"), [(Just(5), "Just(v=5)"), (Nothing(), "Nothing()")])
def test_repr[T](option: Option[T], expected: str):
    assert repr(option) == expected


@pytest.mark.parametrize(
    "fn",
    [
        Nothing().bind,
        Nothing().map,
        Just(5).just_or,
    ],
)
def test_side_effects(fn: Callable):
    mock = Mock()
    fn(mock)
    assert mock.call_count == 0
