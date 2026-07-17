# fnkit

[![PyPI version](https://img.shields.io/pypi/v/fnkit)](https://pypi.org/project/fnkit/)
[![Python versions](https://img.shields.io/pypi/pyversions/fnkit)](https://pypi.org/project/fnkit/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/github/actions/workflow/status/vmuminov/fnkit/tests.yml?label=tests)](https://github.com/vmuminov/fnkit/actions)

Typed functional programming primitives for Python 3.14, built on native PEP 695 generics.

`Option`, `Result`, and `State` give you composable, type-checked alternatives to `None`
checks, exception-driven error handling, and hand-rolled state threading, without a
class hierarchy to inherit from and without losing type information along the way.

## Why this exists

Most Python functional-programming libraries predate PEP 695 and still lean on
`TypeVar` and `Generic[T]`. This library is built from the ground up on Python 3.14's
native generic syntax (`class Foo[T]`, `def bar[T, E = Default]`), structural
`Protocol`s instead of inheritance, and `match` statements for unwrapping values.

## Features

- **`Option[T]`**: a `Just` / `Nothing` pair for values that may or may not exist,
  replacing `None`-based optionality with a type-checked container.
- **`Result[T, E]`**: an `Ok` / `Err` pair for computations that may fail, replacing
  exception-driven control flow with explicit, inspectable failure values.
- **`State[S, A]`**: a composable wrapper around `S -> (A, S)` functions, for
  threading state through a pipeline without mutation or global variables.
- **Monad transformers** (`o_bindt`, `r_bindt`): compose `State` with `Option` or
  `Result` directly, so a stateful computation can short-circuit on `Nothing` or
  `Err` without manual unwrapping at every step.
- **`map` / `bind` / `lift`** across all three types, for a consistent functional
  interface regardless of which container you are working with.
- Fully immutable: every type is a frozen, slotted dataclass. No shared mutable
  state, no reference cycles.
- Structural typing throughout: `Option`, `Result`, and `State` are `Protocol`s, so
  you can write your own conforming implementations without subclassing.

## Requirements

Python 3.14 or later.

## Installation

```bash
uv add fnkit
```

## Quick examples

### Option

```python
from fnkit.option import Just, Nothing, Option, pure

def find_user(name: str) -> Option[str]:
    return Just(name) if name == "ada" else Nothing()

result = (
    find_user("ada")
    .map(str.upper)
    .bind(lambda name: Just(f"hello, {name}"))
    .just_or(lambda: "user not found")
)
print(result)  # hello, ADA
```

### Result

```python
from fnkit.result import Err, Ok, Result

def parse_positive(raw: str) -> Result[int, str]:
    value = int(raw)
    return Ok(value) if value > 0 else Err(f"{value} is not positive")

result = (
    parse_positive("42")
    .map(lambda n: n * 2)
    .map_err(lambda e: f"parse failed: {e}")
    .ok_or(lambda e: -1)
)
print(result)  # 84
```

### State

```python
from fnkit.state import State, pure

def push[T](item: T) -> State[list[T], None]:
    def run(stack: list[T]) -> tuple[None, list[T]]:
        return None, [*stack, item]
    return State(run)

def pop[T]() -> State[list[T], T]:
    def run(stack: list[T]) -> tuple[T, list[T]]:
        return stack[-1], stack[:-1]
    return State(run)

program = push(1).bind(lambda _: push(2)).bind(lambda _: pop())
value, final_state = program.run_state([])
print(value, final_state)  # 2 [1]
```

### Combining State with Result or Option

```python
from fnkit.result import Err, Ok, Result
from fnkit.state import State
from fnkit.transformers import r_bindt

def read_and_validate(state: State[int, Result[int, str]]) -> State[int, Result[int, str]]:
    def validate(value: int) -> State[int, Result[int, str]]:
        if value < 0:
            return State(lambda s: (Err("negative value"), s))
        return State(lambda s: (Ok(value * 2), s))

    return r_bindt(state, validate)
```

## Design notes

- `Nothing`, `Ok`, and `Err` compare and hash by value, not by identity, since all
  three are plain frozen dataclasses.
- `State` compares and hashes by function identity, since two closures cannot be
  compared for behavioral equality in general. Do not rely on `State() == State()`
  for anything other than the same object.
- `lift` for `Option` and `Result` evaluates its first argument before its second,
  so when both sides are `Nothing`/`Err`, the first argument's failure is the one
  that propagates. This matches left-to-right short-circuiting.


## Running tests

```bash
make verify
```

## License

MIT. See `LICENSE` for the full text.
