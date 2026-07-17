from collections.abc import Callable

import pytest

from fnkit.state import State, lift, pure


def test_pure():
    expected = 42
    pured: State[str, int] = pure(42)
    assert isinstance(pured, State)
    actual, state = pured.run_state("67")
    assert actual == expected
    assert state == "67"


@pytest.mark.parametrize(
    ("state", "fn", "inp", "expected"),
    [
        (State(lambda _: (42, None)), lambda val: val + 1, None, (43, None)),
        (State(lambda a: (f"p{a}", a)), lambda val: val.startswith("p"), "A", (True, "A")),
        (State(lambda x: (x, x + 1)), lambda x: x - 5, 100, (95, 101)),
    ],
)
def test_map[S, A, B](state: State[S, A], fn: Callable[[A], B], inp: S, expected: tuple[B, S]):
    assert state.map(fn).run_state(inp) == expected


def test_bind():
    def state2(y: int) -> State[int, int]:
        return State(lambda x: (x + y, x))

    state1 = State(lambda x: (x, x * 5))

    assert state1.bind(state2).run_state(1) == (6, 5)


def test_map_state():
    state: State[int, str] = State(lambda x: (x, x * 5))
    mapped: State[str, str] = state.map_state(str, int)

    assert mapped.run_state("1") == (1, "5")


def test_lift():
    state1 = State(lambda s: (s + 5, s - 1))
    state2 = State(lambda s: (str(s), s))
    assert lift(lambda a, b: (a, b))(state1, state2).run_state(1) == ((6, "0"), 0)
