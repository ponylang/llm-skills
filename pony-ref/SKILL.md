---
name: pony-ref
description: Load the Pony language reference (capabilities, PonyCheck, stdlib pitfalls, mort pattern). Use /pony-ref to load before Pony coding sessions.
disable-model-invocation: false
---

# Pony Language Reference

## Reference Capabilities Quick Reference

| Cap   | Aliases | Read | Write | Share across actors | Use case |
|-------|---------|------|-------|---------------------|----------|
| `iso` | none    | yes  | yes   | yes (by moving)     | Isolated mutable data to send between actors |
| `trn` | box     | yes  | yes   | no                  | Mutable, will become immutable later |
| `ref` | ref     | yes  | yes   | no                  | Normal mutable data within an actor |
| `val` | val     | yes  | no    | yes                 | Immutable, shareable |
| `box` | box/val | yes  | no    | no                  | Read-only view (accepts ref or val) |
| `tag` | any     | no   | no    | yes                 | Identity only, opaque reference |

## Capability Subtyping

- `iso^` (ephemeral) can become anything
- `trn^` can become `ref`, `val`, or `box`
- `ref <: box <: tag`
- `val <: box <: tag`
- `iso <: tag` (non-ephemeral iso can only become tag)
- `trn <: box` (non-ephemeral trn can only become box)

## Key Patterns

**Consuming iso/trn**: Use `consume` to move ownership and enable capability conversion:
```pony
var a: String iso = "hello".clone()
var b: String val = consume a  // a is now unusable
```

**Recover blocks**: Lift capability of result when inner aliases are sendable:
```pony
let s: String iso = recover iso String.create() end
```

**Automatic receiver recovery**: Can call `ref` methods on `iso`/`trn` if all args are sendable:
```pony
let s: String iso = "hello".clone()
s.append(" world")  // works because " world" is val (sendable)
```

**Destructive read for fields**: Can't consume fields, but can swap:
```pony
var old_value: Foo iso = _field = new_value  // returns old value
```

## Method Chaining (`.>`)

The `.>` operator calls a method but returns the receiver instead of the method's return value. This enables fluent chaining on types with mutating methods that return `None` (or any unwanted return):

```pony
// Without chaining — repeating the receiver on every line
let buf = Array[U8]
buf.append("HTTP/1.1")
buf.push(' ')
buf.append("200 OK")
buf.append("\r\n")

// With chaining — receiver flows through
let buf = Array[U8]
buf.>append("HTTP/1.1")
  .>push(' ')
  .>append("200 OK")
  .>append("\r\n")
```

Works with constructors too — `String.>append("hello").>append(" world")` creates a String, appends to it, and the whole expression evaluates to the String.

**When NOT to chain**: Don't use `.>` when you need the method's actual return value. `.>` discards the return and gives you the receiver back instead.

## Common Gotchas

1. **iso to box/ref**: Can't alias `iso` as readable without consuming. Use `consume` to get `iso^` which can become anything.

2. **String.from_iso_array returns iso**: Must `consume` before using in operations expecting `box`:
   ```pony
   var s = String.from_iso_array(consume data)
   s.strip()
   env.out.print("Result: " + consume s)
   ```

3. **Stdin is async**: Use `InputNotify` interface. Buffer input until newline for line-based input.

4. **Actor constructors return tag**: Actors are always `tag` capability from outside.

5. **Default capabilities**: Classes default to `ref`, primitives to `val`, actors to `tag`.

6. **`_` scoping depends on what it's on**: `_field` (leading underscore on a field) is **type-private** — only accessible within the same type. `_method` (leading underscore on a method, constructor, or behavior) is **package-private** — accessible by any type in the same package but not outside it. `_Type` (leading underscore on a type name) is also **package-private**. This distinction matters: you CAN call `SomeType._helper()` from another type in the same package (including tests), but you CANNOT read `SomeType._field` from outside the type.

7. **Type aliases support docstrings**: A docstring string literal inside a `type` alias compiles and is included in generated documentation, just like classes and primitives.

8. **`consume` requires a variable or field, not an expression**: `consume some_method()` is a compile error. Assign the result to a `let` first, then consume (or just assign directly when the target capability allows it). For example, when a method returns `String iso^`, `let s: String val = the_method()?` works directly — ephemeral `iso^` can be assigned to `val` without an explicit `consume`.

9. **Don't use marker traits to group variants**: When a trait carries no methods and exists only to group a closed set of types (e.g., `trait val MyError` with several primitives `is MyError`), use a union type instead (`type MyError is (ErrA | ErrB | ErrC)`). Marker traits are open — anyone can implement them — so the compiler can't enforce exhaustive matching. Union types are closed and enable `match \exhaustive\`, producing compile errors when a variant is unhandled. Reserve traits for when you actually need openness.

10. **Actor constructors cannot fail**: Actor constructor calls return immediately and always succeed from the caller's perspective — there is no way to signal a construction failure. If a partial function's error path would leave the actor in an invalid or unusable state, move the fallible work before actor creation: validate and prepare all inputs in the calling code first, then pass only known-good data to the constructor. This is the "supply chain" pattern — the actor's constructor receives pre-validated inputs, so it never needs to handle errors that would compromise its integrity.

11. **Prefer `embed` over `let` for class/struct fields**: When a field's type is a class or struct and it's initialized from a constructor expression, use `embed` instead of `let`. `embed` is the recommended default — it avoids a pointer indirection and a separate heap allocation. Only use `let` when the field might outlive its parent (exterior references would prevent GC of the parent object), or when the type is an interface, trait, primitive, or numeric type (which can't be embedded).

## Integer Arithmetic Modes

Pony integers have **three** arithmetic modes — choose based on how you want to handle overflow:

| Mode | Operators/Methods | Overflow behavior | Use case |
|------|-------------------|-------------------|----------|
| **Wrapping** (default) | `+`, `-`, `*`, `/`, `%` | Silent wrap-around | When overflow is impossible or harmless |
| **Partial** | `+?`, `-?`, `*?`, `/?`, `%?`, `%%?` | Errors (`?`) | When overflow means invalid input |
| **Checked** | `addc()`, `subc()`, `mulc()`, etc. | Returns `(result, Bool)` | When you need to branch on overflow |

**Partial methods**: `add_partial()`, `sub_partial()`, `mul_partial()`, `div_partial()`, `rem_partial()`, `mod_partial()`. Also `fld_partial()`, `mod_partial()` on signed types. Division by zero also errors.

**Checked methods**: `addc()`, `subc()`, `mulc()`, `divc()`, `remc()`. Also `fldc()`, `modc()` on signed types. The Bool in the return tuple is `true` when overflow/underflow (or division by zero) occurred.

**Common pattern** — accumulating digits with overflow detection:
```pony
// Errors if the accumulated value overflows I64
result = result.mul_partial(10)?.add_partial(digit.i64())?
```

## Syntax Essentials

```pony
actor Main                          // Actor definition
  let _env: Env                     // Immutable field (underscore = private)
  var _count: U32 = 0               // Mutable field with default

  new create(env: Env) =>           // Constructor
    _env = env

  be some_behavior(x: U32) =>       // Behavior (async message handler)
    _count = _count + x

  fun ref mutating_method(): U32 => // Method that can modify state
    _count = _count + 1
    _count

  fun box readonly_method(): U32 => // Read-only method
    _count

class MyClass
  fun apply(): String => "called"   // Makes instances callable: obj()

interface Printable                 // Structural typing
  fun string(): String

trait Named                         // Nominal typing (must explicitly implement)
  fun name(): String

primitive Utils                     // Singleton, default cap is val
  fun helper(): U32 => 42
```

## PonyCheck (Property-Based Testing)

**Two ways to write property tests**:
- `Property1[T]` trait (standalone class, recommended for reusable properties) — implement `name()`, `gen()`, `property()`, register with `test(Property1UnitTest[T](MyProperty))`
- `PonyCheck.for_all` (inline lambdas within a `UnitTest`) — convenient for quick one-offs, but generators must be `val`: `recover val Generators.u8() end`

**Custom generator pattern**: Custom generators MUST be anonymous objects, not named primitives or classes. The correct pattern is always:
```pony
fun gen(): Generator[String] =>
  Generator[String](
    object is GenObj[String]
      fun generate(r: Randomness): String^ =>
        "my value"
    end)
```
Do NOT try `primitive MyGen is GenObj[String]` or `class MyGen is GenObj[String]` — this is a common Claude mistake that produces confusing compiler errors ("can't find definition of 'T'"), which then gets misattributed to a compiler bug. It's a usage error. Return either a bare value or `(value, shrink_iterator)` tuple from `generate()`.

**Generator composition**: `.filter()`, `.map()`, `.flat_map()`, `.union()`, plus `Generators.zip2/3/4`, `Generators.map2/3/4`, `Generators.frequency` (weighted selection).

**Useful built-ins to remember**:
- `IntProperty` trait — tests a property across all 14 Pony integer types automatically
- ASCII range types (`ASCIIPrintable`, `ASCIILetters`, `ASCIIDigits`, etc.) for controlling string generation character sets
- `Generators.one_of` for selecting from a fixed set, `Generators.frequency` for weighted selection

**Gotchas**:
- `flat_map` shrinking is incomplete (TODO in source) — only shrinks on inner generator, not outer
- Collection shrinking generates fresh random elements, just fewer — shrunken collections are NOT subsets of the original
- No built-in `F32`/`F64` generators — use `Generators.repeatedly` with a lambda as workaround
- Seed is printed in test output — pass back via `PropertyParams(where seed' = N)` to reproduce a failure
- **`value.clone()` in `for_all` lambdas**: Generated `String` values arrive as `ref` capability inside `for_all` lambdas. To use them inside `recover val` blocks (e.g., building a `val` array of tuples), call `value.clone()` first — `clone()` on a `ref` returns an `iso^` which can be consumed into the `recover` block. Without this, the `ref` alias prevents the block from lifting to `val`.
- **`Generators.array_of[T]` produces `ref` arrays, not `val`**: `Generators.array_of[U8](Generators.u8())` yields `Generator[Array[U8] ref]`, which can't be used in `zip2`/`map2` when the target type needs `Array[U8] val`. Workaround: use `Generators.map2` with a fill byte + length, constructing the `val` array inside the lambda: `{(fill, len) => (fill, recover val Array[U8].init(fill, len) end)}`.

**PropertyParams defaults**: 100 samples, 10 max shrink rounds, 5 max generator retries, 60s timeout, non-async. Override by implementing `params()` on your Property trait.

## Stdlib Pitfalls and Patterns

- **Use `constrained_types` for validated wrappers**: When you need a type that enforces a domain constraint (e.g., a value within a range, a string matching a pattern), use the `constrained_types` stdlib package instead of writing a class with a partial constructor. Define a `Validator` primitive, then alias `Constrained[T, MyValidator]` and `MakeConstrained[T, MyValidator]`. This returns `(Constrained[T, V] | ValidationFailure)` with descriptive error messages — better than a bare `error` from a partial constructor. Only `val` types can be constrained. See the [Constrained Types](https://patterns.ponylang.io/domain-modeling/constrained-types.md) pattern for the full approach.
- **`Reader.skip(n)` vs `Reader.block(n)` for discarding data**: `block(n)` allocates an `Array[U8]` of size n; `skip(n)` just advances the cursor. When you don't need the bytes, always use `skip`.
- **Zero-copy chain: `Array[U8] val.trim()` + `String.from_array()`**: `trim` on a `val` array returns a shared view (no data copy). `String.from_array` reuses the data pointer. Together they give zero-copy from buffer to decoded String.
- **`Array.shift()` is O(n), `List.shift()` is O(1)**: `Array.shift()` calls `delete(0)` which moves all elements. For chunk-based readers or queues consuming from the head, use `List`.
- **`buffered.Writer` has no `i8` method**: Has `u8`, `i16_be`, `i32_be`, `i64_be`, `f32_be`, `f64_be` but not `i8`. Write a signed byte with `w.u8(I8(-5).u8())`.
- **Semicolons in multi-line array literals**: `[as U8: 1; 2;\n 3; 4]` is a compile error — semicolons at line-continuation points are rejected. All semicolon-separated elements must be on the same line, or use a `recover val` block with the array literal on one line.
- **`block(0)` edge case in chunk-based readers**: When implementing a chunk-based reader, `block(0)` can be called after all chunks are consumed (e.g., zero-length string payloads in msgpack). Must short-circuit and return an empty array before accessing the chunk list.

## Byte-by-Byte Copying is a Design Smell

When you find yourself copying data one byte at a time — manual loops, `append`/`concat` on `Array[U8]`, building a new array element by element — stop and ask why. The usual cause: the reference capabilities don't line up for a bulk operation like `copy_from` or zero-copy `trim`, so you fell back to the slow path to make it compile.

The fix is almost never "accept the byte-by-byte copy." Instead, trace back to where the capability mismatch originates and redesign:
- Can the source data be `val` instead of `ref` so `trim` gives a zero-copy view?
- Can you `recover` earlier to get the right capability at the point where bulk copying happens?
- Can you restructure ownership so the data doesn't need copying at all?
- Can you use `copy_from` instead of `append`/`concat`? (`copy_from` is `memcpy`; `append`/`concat` copy byte-by-byte in a loop. `copy_from` is only available for `Array[U8]`.)

Byte-by-byte is the last resort, not the first workaround. If the refcaps won't cooperate, that's the type system telling you the data flow needs rethinking, not that you need a slower algorithm. If you can't figure out how to make bulk operations work, ask — that's far better than silently inserting a slow copy path.

## Panic Primitives ("Mort" Pattern)

**Panic primitives for impossible code paths**: When the compiler requires a branch that should never execute (e.g., `else` in a `try` after prior size validation), use a panic primitive instead of silently returning a value. The primitive prints file/line to stderr via FFI and exits. Common variants express intent:
- `Unreachable` — compiler can't prove it, but we're certain it's dead code
- `IllegalState` — state machine violation, function called in wrong state
- New variants can be added as needed to express other intents

Implementation: uses `@fprintf`/`@exit`/`@pony_os_stderr` FFI, takes `SourceLoc = __loc` for automatic location, includes project issues URL. A dummy return value may be needed after the call since the compiler doesn't know the primitive diverges. Group multiple variants in a `_mort.pony` file; use `unreachable.pony` for a single primitive. Public or private (`_Unreachable`) depending on package visibility needs. Use `ifdef debug then ... end` wrapper for less-certain cases.

## Deep Reference Material

For deeper type system and runtime questions, read files in the `references/` directory alongside this skill. Start with `type-system-synopsis.md` for a distilled overview, then consult specific papers as needed.

### C-FFI

For C interop questions (calling C from Pony, passing pointers, callbacks, structs for FFI, error handling across the boundary), read `references/tutorial-llms-full.txt` (search for "C-FFI"). For FFI initialization and resource cleanup patterns, read `references/patterns-llms-full.txt` (search for "FFI Global Initializer", "FFI Resource Lifecycle", or "Static Constructor").

### Async and Actor Interaction Patterns

For questions about getting values back from actors, batching work, or coordinating between actors, read `references/patterns-llms-full.txt`. Key sections: "Accessing an Actor with Arbitrary Transactions", "Interrogating Actors with Promises", "Batch and Yield", "Waiting". The Promises pattern is especially common — it solves "how do I get a result from an actor?"

### Compiler Error Messages

Pony's compiler errors can be cryptic. For help interpreting them, read `references/tutorial-llms-full.txt` (search for "A Short Guide to Pony Error Messages").

### Compiler Annotations and Platform-Dependent Code

For `ifdef`/`else` conditionals, `\nodoc\`, `\nosupertype\`, and other annotations, read `references/tutorial-llms-full.txt` (search for "Platform-dependent Code" and "Program Annotations").

### Pattern Cookbook

`references/patterns-llms-full.txt` organizes idiomatic Pony patterns by category. When looking for "how do I..." answers, search by category:

- **Asynchronous** — actor transactions, promises, batch-and-yield, waiting/timers
- **State Machine** — trait-based state machines
- **Code Sharing** — embed/delegate, mixin, notifier, object algebra
- **Creation** — FFI global initializer, static constructor, supply chain, typed step builder
- **Data Sharing** — copying, isolated fields, persistent data structures
- **Error Handling** — error as union type
- **Object Capabilities** — authority hierarchy, single-use capabilities
- **Resource Management** — FFI resource lifecycle
- **Streaming** — peek before consume
- **Testing** — notifier interactions, output-only actors

### Performance

For performance questions, read `references/website-llms-full.txt` (search for "Performance Cheat Sheet") and `references/patterns-llms-full.txt` (search for "performance/"). These cover allocations, boxing, GC tuning, scheduler threads, OS tuning, and profiling.

### Synopses

`references/type-system-synopsis.md` — Distilled reference covering all six capabilities, the deny-properties matrix, subtyping lattice, ephemeral modifiers, aliasing/unaliasing, local and global compatibility tables, viewpoint adaptation (non-extracting and extracting), safe-to-write rules, recovery, generics with capability constraints, and the Steed vs. PonyS differences. **Read this first** for any formal type system question.

`references/runtime-gc-synopsis.md` — Distilled reference covering ORCA (object GC), MAC (actor cycle collection), per-actor heaps, reference count invariant, causal messaging, weighted reference counting, the scheduler, pool allocator, and how the type system enables the runtime. **Includes an "Implementation Divergences" section** documenting where the current ponyc runtime has evolved beyond the papers. Read this first for any runtime or GC question.

### Pony Documentation (from websites)

Each site provides an `llms.txt` (table of contents / synopsis) and an
`llms-full.txt` (complete content). Start with the synopsis; read the full
version when you need detail on a specific topic.

| Site | Synopsis | Full content | Topics |
|------|----------|-------------|--------|
| Tutorial (tutorial.ponylang.io) | `tutorial-llms.txt` | `tutorial-llms-full.txt` | Language guide: types, expressions, reference capabilities, generics, packages, testing, C-FFI, runtime, gotchas |
| Patterns (patterns.ponylang.io) | `patterns-llms.txt` | `patterns-llms-full.txt` | Idiomatic patterns: async, state machines, code sharing, creation, data sharing, error handling, performance, testing |
| Website (www.ponylang.io) | `website-llms.txt` | `website-llms-full.txt` | FAQ, tooling guides (corral, cross-compilation, debugging), philosophy, reference capabilities overview |

These files are snapshots and should be periodically refreshed from the
live websites.

### Papers Index

| Paper | File | Key topics |
|-------|------|------------|
| Steed, "A Principled Design of Capabilities in Pony" (2016) | `a-principled-design-of-capabilities.md` | The active formalization (PonyG). Extracting viewpoint adaptation, active/passive temporaries, uniform well-formedness, Prolog-verified lemmas. Found data-race bug in intersection types. |
| Clebsch et al., "Deny Capabilities for Safe, Fast Actors" (2015) | `deny-capabilities.md` | The foundational paper (PonyS). Deny-properties matrix, all six capabilities, viewpoint adaptation, safe-to-write, aliasing, recovery, core safety invariants. |
| Clebsch et al., "Deny Capabilities" (extended version with proofs) | `deny-capabilities-with-proof.md` | Extended version of the above with full proofs. |
| Lietar, "Formalizing Generics for Pony" (2017) | `formalizing-generics.md` | Extends PonyG with generics (PonyPL). Partial reification technique. Found compiler unsoundness bugs. |
| Clebsch, "Co-Designing a Type System and a Runtime" (PhD thesis, 2017) | `co-designing-type-system-and-runtime.md` | Comprehensive formalization: type system + ORCA + MAC. Deep viewpoint adaptation. Proves preservation and data-race freedom. |
| Clebsch et al., "Orca: GC and Type System Co-Design" (OOPSLA 2017) | `orca-gc.md` | How type system guarantees enable per-actor GC without stop-the-world, read/write barriers, or synchronization. |
| Clebsch et al., "Fully Concurrent Garbage Collection of Actors on Many-Core Machines" | `fully-concurrent-gc.md` | MAC protocol for concurrent actor GC. |
| Clebsch & Blessing, "Ownership and Reference Counting based Garbage Collection in the Actor World" | `ownership-gc.md` | OGC/Pony-ORCA: ownership and reference counting for actor GC. |
| Clebsch et al., "A String of Ponies" | `a-string-of-ponies.md` | Transparent distributed programming with actors. |
