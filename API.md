# fnkit API reference

This document describes every public type and function in `fnkit`, module by
module. For a quick-start overview and installation instructions, see
[README.md](README.md).

## Table of contents

- [fnkit.option](#fnkitoption)
- [fnkit.result](#fnkitresult)
- [fnkit.state](#fnkitstate)
- [fnkit.collection](#fnkitcollection)
- [fnkit.transformers](#fnkittransformers)

---

## fnkit.option

### `Option[T]`

`None` is Python's built-in way of saying "there might not be a value here,"
but it carries no type information about *why* a value is missing, and nothing
stops a `None` from silently propagating through a chain of calls until it
crashes somewhere far from where it originated with an unhelpful
`AttributeError: 'NoneType' object has no attribute ...`.

`Option[T]` makes optionality part of the type itself. A value is either
`Just(v)`, wrapping a real `T`, or `Nothing()`, an explicit, structurally
identical "no value" marker. Because both variants expose the same interface,
you can chain operations on an `Option` without ever writing an `if value is
None` check; the absence of a value is handled by the same `map`/`bind` calls
you'd use for the presence of one.

`Option` is declared as a `Protocol`, not a base class, and is
`@runtime_checkable`. You can write your own conforming type without
inheriting from anything, and `isinstance(x, Option)` works against any object
that structurally exposes `map`, `bind`, and `just_or`.

#### Methods

- **`map[U](self, fn: Callable[[T], U]) -> Option[U]`**
  Applies `fn` to the wrapped value if one exists, and does nothing (returns
  `Nothing()` unchanged) if it doesn't. This is how you transform a value
  without ever handling the missing case explicitly.

  ```python
  Just(5).map(str)        # Just("5")
  Nothing().map(str)      # Nothing()
  ```

- **`bind[U](self, fn: Callable[[T], Option[U]]) -> Option[U]`**
  Like `map`, but `fn` itself returns an `Option`, so you can chain operations
  that might themselves produce "no value" without ending up with a nested
  `Option[Option[U]]`.

  ```python
  Just(5).bind(lambda v: Just(v + 1) if v > 0 else Nothing())  # Just(6)
  ```

- **`just_or(self, fn: Callable[[], T]) -> T`**
  Unwraps the value if present, otherwise calls `fn` and returns its result.
  This is the only place an `Option` chain has to "commit" to a concrete `T`;
  everything before this can stay wrapped.

  ```python
  Just(5).just_or(lambda: 0)     # 5
  Nothing().just_or(lambda: 0)   # 0
  ```

### `pure`

```python
def pure[T](v: T) -> Option[T]
```

Wraps a bare value in the minimal `Option` context, i.e. `Just(v)`. Useful
when you have a plain value partway through a pipeline built entirely out of
`Option`-returning functions and need to lift it into that context to keep
composing.

### `lift`

```python
def lift[A, B, C](fn: Callable[[A, B], C]) -> Callable[[Option[A], Option[B]], Option[C]]
```

Takes an ordinary two-argument function and turns it into one that operates on
two `Option`s at once, short-circuiting to `Nothing()` if either side is
missing. This is the same idea as `liftM2` (or `liftA2`) in Haskell and
similar languages: it lifts a function of plain values into a function of
wrapped values, without you having to manually `bind` through both arguments
yourself.

```python
lift(operator.add)(Just(1), Just(2))   # Just(3)
lift(operator.add)(Nothing(), Just(2)) # Nothing()
```

`lift` evaluates its first argument before its second, so when both sides are
`Nothing()`, the first argument's absence is what propagates.

### `Just`

The concrete "value present" variant of `Option`. A frozen dataclass holding a
single field, `v`, so two `Just` instances with equal values compare and hash
as equal.

### `Nothing`

The concrete "value absent" variant of `Option`. Carries no data. All
`Nothing()` instances compare and hash as equal to each other, regardless of
the `T` they're parameterized over, since there's no value to distinguish them
by.

---

## fnkit.result

### `Result[T, E]`

Exceptions are Python's default way of signaling failure, but they're
invisible in a function's type signature: nothing about `def parse(s: str) ->
int` tells you it can raise `ValueError`, so callers either read the source,
consult the docs, or find out at runtime. `Result[T, E]` puts failure into the
type itself. A computation either succeeds with `Ok(value)` or fails with
`Err(error)`, and both are ordinary values you can inspect, transform, and
pass around, rather than control-flow events that unwind the stack.

What `E` should be is up to you, and different codebases lean on different
conventions. The most common patterns:

- A plain `str` error message, when the failure just needs to be reported to a
  human (`Result[int, str]`).
- A subclass of `Exception`, when you want to keep exception-style error
  hierarchies but stop using `raise`/`except` to move them around
  (`Result[int, ValueError]`).
- A small `enum.Enum` of named failure modes, when the caller needs to branch
  on *which* failure occurred (`Result[int, ParseError]` where `ParseError`
  is an enum).
- A dedicated frozen dataclass carrying structured failure context (an error
  code, a field name, a retry hint), when a bare string or exception doesn't
  carry enough information for the caller to act on.

This pattern is often called **railway-oriented programming**: picture two
parallel tracks, a success track and a failure track, running alongside each
other through your pipeline. Each `map`/`bind` call is a section of track that
only exists on the success side; a value on the failure track skips over all
of them and rides straight through to the end. `Result` is exactly this
model, `map` operates on the success track only, `map_err` on the failure
track only, and once a computation switches onto the failure track, it stays
there.

Like `Option`, `Result` is a `Protocol`, `@runtime_checkable`, and requires no
inheritance to implement.

#### Methods

- **`map[U](self, fn: Callable[[T], U]) -> Result[U, E]`**
  Transforms the success value, does nothing to a failure.

  ```python
  Ok(5).map(str)         # Ok("5")
  Err("boom").map(str)   # Err("boom")
  ```

- **`map_err[F](self, fn: Callable[[E], F]) -> Result[T, F]`**
  Transforms the failure value, does nothing to a success. This is the
  failure-track counterpart to `map`.

  ```python
  Err("boom").map_err(str.upper)  # Err("BOOM")
  Ok(5).map_err(str.upper)        # Ok(5)
  ```

- **`bind[U](self, fn: Callable[[T], Result[U, E]]) -> Result[U, E]`**
  Chains a `Result`-returning computation onto a success, short-circuits on a
  failure. Use this whenever the next step of the pipeline can itself fail.

  ```python
  Ok(5).bind(lambda v: Ok(v * 2) if v > 0 else Err("not positive"))  # Ok(10)
  ```

- **`ok_or(self, fn: Callable[[E], T]) -> T`**
  Unwraps the success value, or calls `fn` with the failure value to produce a
  fallback `T`. This is where a `Result` chain commits to a concrete value.

  ```python
  Ok(5).ok_or(lambda e: -1)          # 5
  Err("boom").ok_or(lambda e: -1)    # -1
  ```

### `pure`

```python
def pure[T, E = Exception](v: T) -> Result[T, E]
```

Wraps a bare value as `Ok(v)`. `E` defaults to `Exception` via a PEP 696 type
parameter default, so `pure(5)` infers as `Result[int, Exception]` unless a
call site narrows it explicitly (`pure[int, ValueError](5)`), or the
assignment context does it for you.

### `lift`

```python
def lift[A, B, C, E](fn: Callable[[A, B], C]) -> Callable[[Result[A, E], Result[B, E]], Result[C, E]]
```

The `Result` counterpart to `liftM2`/`liftA2`: takes a plain two-argument
function and produces one that operates on two `Result`s, short-circuiting to
whichever side fails first. As with `Option`'s `lift`, the first argument is
evaluated before the second, so when both sides are `Err`, the first
argument's error is the one that propagates.

```python
lift(operator.add)(Ok(1), Ok(2))       # Ok(3)
lift(operator.add)(Err("a"), Err("b")) # Err("a")
```

### `Ok`

The success variant. A frozen dataclass holding one field, `v` (the success
value), plus the `E` type parameter carried purely for typing purposes.

### `Err`

The failure variant. A frozen dataclass holding one field, `v` (the failure
value, of type `E`), plus the `T` type parameter carried purely for typing
purposes.

### `as_result`

```python
def as_result[T, **P](f: Callable[P, T]) -> Callable[P, Result[T, Exception]]
```

Wraps an ordinary, exception-raising function so that it returns a `Result`
instead. The wrapped function calls `f` with whatever arguments it's given;
if `f` returns normally, the result comes back as `Ok(value)`, and if `f`
raises any `Exception`, the exception instance itself is caught and returned
as `Err(exception)` rather than propagating up the stack. This is the
adapter you reach for at the boundary between `fnkit`'s explicit,
railway-oriented error handling and the rest of the Python ecosystem, which
overwhelmingly signals failure by raising.

```python
safe_int = as_result(int)
safe_int("1")    # Ok(1)
safe_int("a")    # Err(ValueError("invalid literal for int() with base 10: 'a'"))
```

Note that `as_result` catches `Exception` and its subclasses broadly, it does
not let you narrow which exception types get converted versus re-raised.
`BaseException` subclasses that aren't `Exception` (`KeyboardInterrupt`,
`SystemExit`) are not caught, and continue to propagate normally.

---

## fnkit.state

### `State[S, A]`

Threading state through a pipeline by hand usually means either mutating a
shared object (which makes functions harder to reason about and test in
isolation) or manually passing a state value in and out of every function
signature (which is correct but tedious and easy to get wrong). `State[S, A]`
wraps this pattern once: a `State` is just a function `S -> (A, S)`, "given
the current state, produce a value and the next state." `map` and `bind` let
you compose these functions without ever touching the state threading
yourself; the plumbing that passes `S` from one step to the next is handled
entirely inside `bind`.

This is also how `State` lets you **model something IO-shaped without
touching real IO**. If you replace "the current state" with "the current
contents of a simulated file," "the current position in a simulated random
number stream," or "the current log of side effects performed so far," you
get a fully pure, deterministic, testable stand-in for a genuinely impure
operation. Your business logic calls `.bind()` the same way whether `S` is an
integer counter or a simulated filesystem; only the function you eventually
pass to `run_state` decides whether that simulated state is ever connected to
anything real.

`State` is not a `Protocol`, it's a concrete frozen dataclass, since there's
only ever one sensible way to represent "a function from state to (value,
state)."

#### Methods

- **`map[B](self, fn: Callable[[A], B]) -> State[S, B]`**
  Transforms the produced value, leaves the state untouched.

  ```python
  State(lambda s: (s, s)).map(lambda a: a + 1).run_state(5)  # (6, 5)
  ```

- **`map_state[Y](self, sy: Callable[[S], Y], ys: Callable[[Y], S]) -> State[Y, A]`**
  Re-parameterizes the state type from `S` to `Y`, given a pair of functions
  converting between them. `sy` and `ys` must be true inverses of each other;
  passing functions that don't round-trip correctly will silently produce a
  `State` whose state doesn't behave as expected, since nothing checks the
  isomorphism for you.

- **`bind[B](self, fn: Callable[[A], State[S, B]]) -> State[S, B]`**
  Chains a `State`-returning computation onto this one, threading the updated
  state from the first computation into the second. This is the core
  composition operator: almost every non-trivial use of `State` goes through
  `bind`.

  ```python
  def push[T](item: T) -> State[list[T], None]:
      return State(lambda s: (None, [*s, item]))

  push(1).bind(lambda _: push(2)).run_state([])  # (None, [1, 2])
  ```

- **`run_state: Callable[[S], tuple[A, S]]`**
  The underlying field itself, the raw function this `State` wraps. Call it
  directly with an initial state to actually execute the computation and get
  back `(value, final_state)`.

### `pure`

```python
def pure[A, S = NoneType](v: A) -> State[S, A]
```

Wraps a bare value as a `State` that ignores whatever state it's given and
passes it through unchanged. `S` defaults to `NoneType` via PEP 696, matching
the common case of "this particular step doesn't care about state at all,"
while still allowing an explicit `S` to be supplied at the call site when it
does.

### `lift`

```python
def lift[A, B, C, S](fn: Callable[[A, B], C]) -> Callable[[State[S, A], State[S, B]], State[S, C]]
```

Lifts a plain two-argument function into one operating on two `State`s. Unlike
`Option`'s and `Result`'s `lift`, this one is not about short-circuiting,
there's no failure case to short-circuit on, it's about **sequencing**: the
first `State` runs against the input state, and whatever state it leaves
behind is exactly the state the second `State` runs against. The order of the
two arguments is not just evaluation order here, it's a correctness
requirement, since the second computation genuinely depends on the state the
first one produced.

```python
a = State(lambda s: (s + 1, s + 10))
b = State(lambda s: (s * 2, s + 100))
lift(operator.add)(a, b).run_state(1)  # a produces (2, 11); b then runs on 11 -> (22, 111); result (24, 111)
```

---

## fnkit.collection

### `Collection[T]`

Python already has a genuinely good, deeply built-in iterator protocol,
generators, `itertools`, lazy evaluation via `map`/`filter`, all of it native
to the language. Rather than reimplementing a `List`/`Vector`-style container
from scratch the way some functional libraries do, `Collection[T]` is a thin
wrapper around `Iterable[T]` that adds the monadic `map`/`bind` interface on
top of whatever iterable you already have, list, tuple, generator, `map`
object, or anything else implementing `__iter__`.

The cost of this thinness is that `Collection` inherits whatever rewindability
its backing iterable has. Wrap a `list` or `tuple` and you can iterate the
same `Collection` repeatedly. Wrap a generator or other one-shot iterator and
the first traversal exhausts it; a second call to `.map()`, `.bind()`, or a
second `for` loop over the same instance will silently produce nothing.
`Collection` does not materialize or cache its contents on your behalf, by
design, to stay lazy wherever it can.

#### Methods

- **`map[U](self, fn: Callable[[T], U]) -> Collection[U]`**
  Lazily applies `fn` to every element. Nothing is computed until the result
  is iterated.

  ```python
  list(Collection([1, 2, 3]).map(str))  # ["1", "2", "3"]
  ```

- **`bind[U](self, fn: Callable[[T], Collection[U]]) -> Collection[U]`**
  Maps `fn` over every element and flattens the resulting collections into
  one, Python's `flatMap`. Also lazy.

  ```python
  list(Collection([1, 2]).bind(lambda x: Collection([x, -x])))  # [1, -1, 2, -2]
  ```

- **`reduce[U](self, fn: Callable[[U, T], U], init: U) -> U`**
  Eagerly folds the collection down to a single value, starting from `init`.
  Unlike `map` and `bind`, this immediately consumes the entire underlying
  iterable.

  ```python
  Collection([1, 2, 3]).reduce(operator.add, 0)  # 6
  ```

- **`__iter__(self) -> Iterator[T]`**
  Delegates directly to the underlying iterable's iterator, so a `Collection`
  can be used anywhere a plain `Iterable` is expected, in a `for` loop, passed
  to `list()`, unpacked, and so on.

### `pure`

```python
def pure[T](v: T) -> Collection[T]
```

Wraps a single bare value as a one-element `Collection` (backed by a
`deque`).

### `lift`

```python
def lift[T, U, V](fn: Callable[[T, U], V]) -> Callable[[Collection[T], Collection[U]], Collection[V]]
```

The `Collection` counterpart to `liftM2`/`liftA2`, but with cartesian-product
semantics rather than short-circuiting or sequencing: it pairs every element
of the first collection with every element of the second and applies `fn` to
each pair.

```python
lift(operator.mul)(Collection([1, 2]), Collection([10, 20]))
# Collection([10, 20, 20, 40])
```

Note that this one is not lazy the way `map`/`bind` are: `itertools.product`
needs to iterate its inputs more than once internally, so it fully
materializes both `c1` and `c2` before producing any output. For very large or
infinite collections, this is worth keeping in mind.

### `sequence`

```python
def sequence(collection: Collection[T]) -> Any  # see overloads below
```

Turns a `Collection` of wrapped values inside out into a single wrapped
`Collection`. Given a `Collection[Result[T, E]]`, `sequence` returns a
`Result[Collection[T], E]`, succeeding with all the values if every element
succeeded, or short-circuiting to the first `Err` encountered. The same idea
applies to `Collection[Option[T]]` and `Collection[State[S, T]]`.

This is the same operation as Haskell's `sequence`/`traverse`, Rust's
`Iterator::collect::<Result<Vec<_>, _>>()`, or Scala's `sequence` on a
collection of `Option`/`Either`: "if every element in this collection is
wrapped, turn the whole collection into one wrapped value; otherwise, tell me
what went wrong and where."

```python
sequence(Collection([Ok(1), Ok(2), Ok(3)]))          # Ok(Collection([1, 2, 3]))
sequence(Collection([Ok(1), Err("bad"), Ok(3)]))     # Err("bad")
```

`sequence` inspects the first element to decide which of `Result`, `Option`,
or `State` it's dealing with, and dispatches accordingly. If the elements
aren't any of those, it returns the `Collection` unchanged. This also means an
**empty `Collection` has no element to inspect**, so `sequence` cannot know
which monad to wrap the result in; rather than introduce a separate Identity
monad solely to make that one case type-correct, `sequence` on an empty
collection returns a bare `Collection` unchanged. This is a documented,
deliberate limitation: if your collection might be empty, check for that
before relying on the wrapped-monad return type.

---

## fnkit.transformers

A **monad transformer** combines two monads into one, so you can operate
through both layers at once instead of manually unwrapping the outer one at
every step just to get at the inner one. Here specifically: a
`State[S, Result[A, E]]` (a stateful computation that might fail) or a
`State[S, Option[A]]` (a stateful computation that might produce nothing) both
require, without a transformer, that you run the `State`, pattern-match on
whether the inner value succeeded, and only then decide whether to run the
next step, by hand, every single time. `r_bindt` and `o_bindt` fold that
pattern-match into the bind itself: give them a `State` of a `Result`/`Option`
and a function producing the next `State` of a `Result`/`Option`, and they
handle the short-circuiting for you.

Why two separate functions rather than one generic transformer? Because
Python has no **higher-kinded types**. Languages that support monad
transformers generically, Haskell's `StateT s (Either e) a`, for instance, can
write a single transformer parameterized over "any monad `m`," because their
type systems can express "a type constructor applied to another type
constructor." Python's generics (including PEP 695's native syntax used
throughout this library) can express "a type parameterized by another type,"
but not "a type parameterized by another type constructor." There is no way to
write one function generic over "`State` composed with an arbitrary monad
`M`" and have it work for both `Result` and `Option` without either losing
type safety or resorting to runtime duck-typing throughout. Splitting the
machinery into one function per concrete pairing is the tradeoff Python's type
system forces here, at the cost of some duplication between `r_bindt` and
`o_bindt`, in exchange for both functions being fully, concretely typed.

### `r_bindt`

```python
def r_bindt[S, A, B, E](
    state: State[S, Result[A, E]],
    fn: Callable[[A], State[S, Result[B, E]]],
) -> State[S, Result[B, E]]
```

Runs `state`, and if its result is `Ok(value)`, runs `fn(value)` against the
resulting state and returns that. If the result is `Err`, short-circuits
immediately, `fn` is never called, and the `Err` (with its state) is returned
as-is.

### `o_bindt`

```python
def o_bindt[S, A, B](
    state: State[S, Option[A]],
    fn: Callable[[A], State[S, Option[B]]],
) -> State[S, Option[B]]
```

The `Option` counterpart to `r_bindt`. Runs `state`, and if its result is
`Just(value)`, runs `fn(value)` against the resulting state and returns that.
If the result is `Nothing`, short-circuits immediately, `fn` is never called,
and `Nothing` (with its state) is returned as-is.
