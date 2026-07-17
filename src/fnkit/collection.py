from collections import deque
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from functools import reduce
from itertools import chain, product, starmap
from typing import Any, overload

from fnkit.option import Option
from fnkit.option import lift as o_lift
from fnkit.option import pure as o_pure
from fnkit.result import Result
from fnkit.result import lift as r_lift
from fnkit.result import pure as r_pure
from fnkit.state import State
from fnkit.state import lift as s_lift
from fnkit.state import pure as s_pure


@dataclass(frozen=True, slots=True)
class Collection[T](Iterable[T]):
    v: Iterable[T]

    def map[U](self, fn: Callable[[T], U]) -> Collection[U]:
        return Collection(map(fn, self.v))

    def bind[U](self, fn: Callable[[T], Collection[U]]) -> Collection[U]:
        return Collection(chain.from_iterable(map(fn, self.v)))

    def reduce[U](self, fn: Callable[[U, T], U], init: U) -> U:
        return reduce(fn, self.v, init)

    def __iter__(self) -> Iterator[T]:
        return iter(self.v)


def pure[T](v: T) -> Collection[T]:
    return Collection(deque((v,)))


def lift[T, U, V](
    fn: Callable[[T, U], V],
) -> Callable[[Collection[T], Collection[U]], Collection[V]]:
    def _inner(c1: Collection[T], c2: Collection[U]) -> Collection[V]:
        zipped = product(c1, c2)
        v = starmap(fn, zipped)
        return Collection(v)

    return _inner


@overload
def sequence[T, E](collection: Collection[Result[T, E]]) -> Result[Collection[T], E]: ...  # pyright: ignore[reportOverlappingOverload]


@overload
def sequence[T](collection: Collection[Option[T]]) -> Option[Collection[T]]: ...


@overload
def sequence[T, S](collection: Collection[State[S, T]]) -> State[S, Collection[T]]: ...


@overload
def sequence[T](collection: Collection[T]) -> Collection[T]: ...


def sequence[T](collection: Collection[T]) -> Any:
    it = iter(collection)
    try:
        current_item = next(it)
    except StopIteration:
        # Known limitation: an empty collection has no element to inspect, so we
        # cannot detect which monad to wrap the result in. We deliberately return
        # a bare Collection[T] here rather than introduce an Identity monad solely
        # to make this one case type-correct.
        return collection

    match current_item:
        case Result():
            elem_pure = r_pure
            elem_lift = r_lift
        case Option():
            elem_pure = o_pure
            elem_lift = o_lift
        case State():
            elem_pure = s_pure
            elem_lift = s_lift
        case _:
            # Same as above - avoiding the Identity monad complexity
            return Collection(chain(deque((current_item,)), it))

    container: deque[T] = deque()

    def append(q: deque[T], v: T) -> deque[T]:
        q.append(v)
        return q

    lifted_append = elem_lift(append)

    return reduce(
        lifted_append,  # type: ignore
        it,  # type: ignore
        lifted_append(elem_pure(container), current_item),  # type: ignore
    ).map(Collection)
