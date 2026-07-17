from collections.abc import Callable
from operator import add
from unittest.mock import Mock

import pytest

from fnkit.result import Err, Ok, Result, as_result, lift, pure


def test_pure():
    pured = pure(5)
    assert isinstance(pured, Ok)
    assert pured.v == 5


@pytest.mark.parametrize(
    ("result", "fn", "v"),
    [
        (Ok(5), str, Ok("5")),
        (Err(5), str, Err(5)),
        (Ok([1, 2, 3]), lambda seq: len(seq) > 0, Ok(True)),
    ],
)
def test_map[T, V, E](result: Result[T, E], fn: Callable[[T], V], v: Result[V, E]):
    assert result.map(fn) == v


@pytest.mark.parametrize(
    ("result", "fn", "v"),
    [
        (Ok(5), str, Ok(5)),
        (Err(5), str, Err("5")),
        (Ok([1, 2, 3]), lambda seq: len(seq) > 0, Ok([1, 2, 3])),
        (Err([1, 2, 3]), lambda seq: len(seq) > 0, Err(True)),
    ],
)
def test_map_err[T, F, E](result: Result[T, E], fn: Callable[[E], F], v: Result[T, F]):
    assert result.map_err(fn) == v


@pytest.mark.parametrize(
    ("result", "fn", "v"),
    [
        (Ok(1), lambda inp: Ok(inp + 3), Ok(4)),
        (Ok(2), lambda _: Err("err"), Err("err")),
        (Err(67), lambda _: Ok("hello"), Err(67)),
        (Err(67), lambda _: Err(69), Err(67)),
    ],
)
def test_bind[T, V, E](result: Result[T, E], fn: Callable[[T], Result[V, E]], v: Result[V, E]):
    assert result.bind(fn) == v


@pytest.mark.parametrize(
    ("result", "fn", "t"),
    [
        (Ok(42), lambda _: 67, 42),
        (Err("42"), int, 42),
    ],
)
def test_ok_or[T, E](result: Result[T, E], fn: Callable[[E], T], t: T):
    assert result.ok_or(fn) == t


@pytest.mark.parametrize(
    ("fn", "first", "second", "result"),
    [
        (add, Ok("abc"), Ok("cde"), Ok("abccde")),
        (add, Ok("abc"), Err(1), Err(1)),
        (add, Err(2), Ok("abc"), Err(2)),
        (add, Err(1), Err(8), Err(1)),
    ],
)
def test_lift[A, B, C, E](
    fn: Callable[[A, B], C], first: Result[A, E], second: Result[B, E], result: Result[C, E]
):
    assert lift(fn)(first, second) == result


def test_eq():
    assert Ok(1) == Ok(1)
    assert Ok(1) != Ok(2)
    assert Ok(1) != Ok(None)
    assert Ok(1) != Err(1)
    assert Err("test") == Err("test")
    assert Err("test") != Err("rest")
    assert Err("test") != Err(None)


def test_hash():
    assert hash(Err("test")) == hash(Err("test"))
    assert hash(Err("test")) != hash(Err("rest"))
    assert hash(Ok(2)) == hash(Ok(2))
    assert hash(Ok(2)) != hash(Ok(4))


@pytest.mark.parametrize(
    "fn",
    [
        Err("error").bind,
        Err("error").map,
        Ok(5).map_err,
        Ok(5).ok_or,
    ],
)
def test_side_effects(fn: Callable):
    mock = Mock()
    fn(mock)
    assert mock.call_count == 0


@pytest.mark.parametrize(
    ("inp", "fn", "exp"),
    [("a", int, Err(ValueError("invalid literal for int() with base 10: 'a'"))), ("1", int, Ok(1))],
)
def test_as_result[T, U](inp: T, fn: Callable[[T], U], exp: U):
    actual = as_result(fn)(inp)
    if isinstance(exp, Err) and isinstance(actual, Err):
        assert type(actual.v) is type(exp.v)
        assert actual.v.args == exp.v.args
        with pytest.raises(type(exp.v)):
            fn(inp)
    else:
        assert actual == exp
