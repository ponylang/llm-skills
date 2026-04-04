---
name: pony-pbt-patterns
description: Property-based and generative testing patterns. Load when writing property-based tests, generators, or generative test suites.
disable-model-invocation: false
---

# Property-Based & Generative Testing Patterns

## 1. The Valid/Invalid/Mixed Generator Triad

For any validated type or input boundary, create three coordinated generators: one that only produces valid inputs, one that only produces invalid inputs, and a mixed generator that wraps both. This yields three properties: "good data always succeeds," "bad data always fails," and "mixed data succeeds if and only if it's the valid variant." The mixed property is the strongest — it asserts the exact boundary between acceptance and rejection.

## 2. Invalid Generators Should Cover Every Failure Mode

Invalid input generators should use the equivalent of `oneof` across distinct failure modes (too short, too long, invalid characters, reserved words, etc.) rather than just generating random bad data. This exercises all rejection branches, not just the easiest-to-hit path.

## 3. Derive Generators from Validation Rules

Build generators mechanically from the same constants and rules the validators use (min/max length, allowed character sets, regexes, etc.). Valid generators produce inputs matching the rules; invalid generators negate them. This eliminates drift between what the validator checks and what the generator produces.

## 4. Compositional Generator Hierarchy

Compose complex generators from simpler validated ones. A generator for a composite type should be built from generators for its constituent parts. Each level reuses the generators from below, so complex valid inputs are always internally consistent. This is the property-based testing equivalent of builder patterns.

## 5. Test from Multiple Angles

Look for ways to verify the same behavior from more than one direction. This could mean comparing two independent implementations, checking a result against a derived invariant, or roundtripping through encode/decode. Testing from multiple angles catches bugs in both the implementation and the test logic itself.

## 6. Balance Edge-Case Coverage Against Iteration Speed

When generating test data, bias toward smaller/simpler inputs for fast feedback while still exercising expensive edge cases (max-size inputs, boundary conditions) at a lower frequency. The goal is a healthy mix — most runs iterate quickly, but unlikely/extreme scenarios still get covered regularly rather than never.

## 7. Supplement Property Tests with Examples for Unreachable Paths

When code dispatches across multiple paths based on value size (format families, encoding tiers, protocol variants), constrained property generators will only cover some paths. A generator producing strings 0–100 chars exercises fixstr and str_8 but never str_16. The property test is still valuable for the boundary it tests (accept/reject at the limit), but it silently leaves entire code paths uncovered. Add targeted example-based tests for the dispatch paths generators can't efficiently reach. This is a specific case of "consistency across repetitive structure" applied to test coverage.
