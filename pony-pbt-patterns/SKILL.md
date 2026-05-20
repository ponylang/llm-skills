---
name: pony-pbt-patterns
description: Property-based and generative testing patterns. Load when writing property-based tests, generators, or generative test suites.
disable-model-invocation: false
---

# Property-Based & Generative Testing Patterns

Property-based testing fails quietly. A generator runs thousands of cases, every one passes, and you conclude the code is correct — when in fact the generator only ever visited a small, central slice of the input space and never went near the bugs.

The core problem this skill addresses: **chance is not coverage.** Left to uniform randomness under one fixed configuration, every generated case is statistically similar to the last — the bulk of any distribution sits in its typical region, and uniform sampling faithfully reproduces that — so the explored region clusters around "typical" values and "typical" sequences. The bugs live at the edges: the empty input, the maximum size, the off-by-one neighbor of a boundary, the structure that grew far larger than any single test usually builds. Uniform sampling reaches those points with vanishing probability, so a green suite tells you the typical case works and almost nothing about the rest.

The job of a good generator is therefore not to be *random* — it is to **structurally bias generation toward where bugs live.** That bias operates at two scales:

- **Values** — the individual numbers, strings, and sizes a generator emits. Uniform sampling over a domain essentially never produces the handful of values where bugs concentrate — the "important values": boundaries, zero and one, min and max, and the like.
- **Emergent state** — the aggregate condition built up by a *sequence* of operations: a stack's depth, a map's size, an account's balance. When every operation is always available, that state does a bounded random walk and hovers near where it started; the deep states stay statistically unreachable unless you change which operations are in play.

This bias matters wherever the code *branches* on a value or *accumulates* state across operations. For a property that holds uniformly across its whole domain — an algebraic law, an encode/decode round-trip — there are no edges to seek out and broad uniform generation is already right. Bias toward where bugs live without starving the ordinary middle, where plenty of logic bugs also sit.

The two scales are cross-cutting lenses, not the document's organizing axis. The patterns below are grouped by the goal you have at the moment: making the generator reach the space chance won't (A), probing a validation boundary precisely (B), and building generators and oracles you can trust (C). They map onto PonyCheck — see `/pony-ref` for its generator API and gotchas.

## A. Reach the space chance won't

These are not a sequence — reach for whichever fits the situation. The first two reshape generation to reach a region; the rest are the constraints on doing so — reshape before falling back to hand-written examples, and keep the common case cheap so the suite stays fast.

### Bias toward important values

Some values are where bugs cluster regardless of the domain. For integers: `0`, `1`, `-1`, the type's `min` and `max`, powers of two, and the neighbor just above and just below every boundary the code branches on. For collections: the empty one, the single-element one, and a very large one. For strings: empty, a single character, the maximum length, a length just past a boundary, and embedded multibyte or control characters. For floats: `NaN`, positive and negative infinity, and `-0.0` — and note that Pony's `NaN == NaN` is `true` (it is *not* IEEE 754 here), so never write a generator or assertion that assumes NaN is unequal to itself.

PonyCheck's numeric generators (`Generators.u64()` and friends) sample *uniformly* across their range and inject none of these values. The only special-value handling PonyCheck does is during shrinking, not generation — so a full-range `Generators.u64()` will, in practice, never hand you `0` or `U64.max_value()`. Build the bias yourself with `Generators.frequency`, weighting a broad uniform generator against a `one_of` over the constants that bite:

```pony
// Mostly the broad uniform range, with the values that bite mixed in (8:1).
Generators.frequency[U64]([
  as WeightedGenerator[U64]:
  (8, Generators.u64())
  (1, Generators.one_of[U64]([U64(0); U64(1); U64.max_value()]))
])
```

`frequency` does the weighting; `one_of` picks uniformly from a fixed list of *values* (not generators) — here, the constants that bite. Each array entry is a `(weight, generator)` tuple, and the `as WeightedGenerator[U64]:` line types the literal so those tuples resolve. Don't reach for `union` here: it is an unweighted 50/50 combine of two *generators*, a different tool for a different job.

PonyCheck ships no float generator, so for floats you build your own — map a `u32()`/`u64()` bit pattern onto a float, or `repeatedly` a hand-built value — and make sure it can emit `NaN`, the infinities, and `-0.0`. For collection sizes, the important values are reached through the size arguments — `min`/`max` on `seq_of`/`array_of`, `max` alone on `set_of` (whose size always starts at zero) — or a `frequency` over sizes, not by hoping the default range happens to land on empty or huge.

### Vary which operations are enabled (swarm testing)

When you test a stateful API by generating a *sequence* of operations, the instinct is to make every operation available on every test, each with some probability. That instinct is wrong, and the reason is the random walk: a stack driven by `push` and `pop` at roughly equal probability is pinned near empty by the floor at size zero, so it almost never grows large enough to expose a reallocation or capacity bug. The bug needs `pop` to be *absent*, and an all-operations-enabled distribution keeps it present in every test.

Swarm testing (Groce et al., 2012) fixes this: instead of one fixed operation set for every test, give each test its own randomly chosen *subset* of the operations, and build the sequence from only that subset. Omission is the mechanism — drop `pop` for a run and the stack runs straight to a huge depth; drop `delete` and the structure only grows. Across the swarm, different tests are pushed into different extremes, and the union explores far more than any single "diverse" all-operations test ever could.

Three things the construction must get right:

- **Build the configuration as one include/exclude choice per operation.** Use one `bool()` per operation — not `one_of`, which picks a single element rather than a subset, nor `Generators.set_of`, which takes a *generator of elements* rather than a fixed set and whose subset can be empty. Guard that degenerate empty configuration: a test with zero operations enabled does nothing, so require at least one enabled, or fall back to the full set.
- **Make the sequence draw only from the enabled operations.** Bind the configuration with `flat_map` so the action-sequence generator — e.g. a `seq_of` whose element generator is `one_of` over the enabled ops — uses only that subset.
- **Carry the configuration into the generated value.** Inside that `flat_map`, `map` the action sequence into a `(config, actions)` pair so the property receives both — a swarm failure is nearly useless if you can't see which operations were enabled. Do *not* use `zip2` to pair them: `zip2` draws its two arguments independently, so the config it reports would not be the one the sequence was actually built from.

On diagnosis: PonyCheck's `flat_map` does not yet shrink the configuration it binds, and sequence shrinking regenerates a fresh, shorter sequence rather than removing operations from the failing one. So treat the printed `(config, actions)` as your primary evidence — don't expect a cleanly minimized counterexample for a swarm failure.

### Spend the budget where bugs live

Uniform sampling won't reach the extremes on its own, so spend part of the budget driving them deliberately — max-size inputs, the boundary values, the deepest sequences — applying "important values" to whatever *large* or *deep* means here. Don't assume a high iteration count substitutes; count alone doesn't change the distribution. The counterweight pulls the other way: keep the common case cheap. Bias the bulk of generation toward small, simple inputs so the suite stays fast, and reserve the expensive extremes for a lower frequency. The tension is deliberate — aim for a healthy mix, not uniform sizing that is both slow and shallow.

### Hand-write examples only for what generation can't reach

When a code path is gated on a value size or shape that a constrained generator won't efficiently produce — a string generator covering 0–100 characters exercises the small and medium encodings but never the 64K-plus variant — that path is silently uncovered. First try to reach it by reshaping generation (widen the range, bias toward the size, swarm the operations). Only when generation genuinely can't reach it cheaply do you fall back to a targeted example-based test for that specific path. Examples are the last resort, not the first answer; a property test that quietly skips a dispatch branch is worse than one you know is example-backed.

## B. Probe the validation boundary precisely

For a validated type, the accept/reject boundary is where the important values live — these patterns are the value-scale bias of group A applied to a boundary defined by rules rather than by a type's range.

### Valid/invalid/mixed generator triad

For any validated type or input boundary, create three coordinated generators: one that only produces valid inputs, one that only produces invalid inputs, and a mixed generator that wraps both. This yields three properties: "good data always succeeds," "bad data always fails," and "mixed data succeeds if and only if it is the valid variant." The mixed property is the strongest — it asserts the exact boundary between acceptance and rejection, not just one side of it.

### Cover every failure mode, not just the easy one

An invalid-input generator should combine a distinct generator per failure mode — too short, too long, invalid characters, reserved words — with `frequency` (it weights across any number of modes; `union` combines only two), rather than emitting generic bad data. Random garbage tends to fail the first check it hits, so the easiest-to-trigger rejection branch gets all the coverage and the others get none. Enumerating the failure modes exercises every rejection path.

### Derive generators from the validation rules

Build generators mechanically from the same constants and rules the validators use — min/max length, allowed character sets, regexes. The valid generator produces inputs matching the rules; the invalid generator negates them. Sharing the source of truth eliminates drift between what the validator checks and what the generator produces, so the test can't silently stop testing the real boundary when a rule changes.

## C. Build generators and oracles you can trust

A generator that builds inconsistent inputs, or an oracle that is wrong in the same way the code is, hands you false confidence. These two patterns keep both honest.

### Compose complex generators from validated parts

Build a generator for a composite type out of the generators for its constituent parts, each of which is itself valid by construction. Every level reuses the level below, so a complex generated value is internally consistent rather than a bag of independently-random fields that may contradict each other. This is the property-based equivalent of a builder pattern.

### Check results from more than one angle

Verify the same behavior from more than one direction: compare against an independent implementation, check the result against a derived invariant, or roundtrip through encode/decode. A single oracle can be wrong in the same way the implementation is wrong; a second, independent angle catches bugs in both the code under test and the test's own logic.
