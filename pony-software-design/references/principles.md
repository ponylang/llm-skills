# Code Design Principles

These are the general code-design principles this skill works from — the design personas use them as background, and the principle-checker verifies a design against them. They are a project-agnostic baseline, alongside this skill's own design disciplines (in `SKILL.md`).

If the project being designed for has its own `AGENTS.md` or other stated conventions, those apply too and take precedence where they conflict with this baseline.

## Principles

1. **Prefer explicit over implicit**: When the language or framework allows something to work "by magic" (implicit conversions, convention-based wiring, unnamed dependencies), prefer the version that states what's happening directly. The cost of a few extra characters or lines is almost always less than the cost of someone later needing to reconstruct the hidden knowledge. Several principles below are specific applications of this idea.

2. **Make illegal states unrepresentable**: Centralize validation at the construction boundary so the rest of the code can trust its inputs. Use the type system where strong (private constructors, factory methods returning error-or-value), conventions where weak. For complex types, separate the raw data shape from a validated wrapper (raw → validation → validated form); the rest of the system works with the validated form.

3. **Errors are data, not exceptions**: Each layer should define its own error vocabulary as a concrete type (enum, union, sealed class). Higher-level errors wrap lower-level ones to preserve full context. Every error type should know how to describe itself as text. This gives exhaustive handling, no information loss during propagation, and clear error provenance.

4. **Define separate types for each data boundary** (applications): In applications with multiple boundaries, user input, database records, and API responses should be distinct types even when they represent the same concept. A database record has an auto-generated ID; user input doesn't. Making these distinct prevents mixing concerns.

5. **Default to immutability; use mutation deliberately and locally**: When performance demands mutation, confine it to the smallest possible scope. The rest of the system shouldn't know or care.

6. **Prefer qualified/namespaced references**: Even when the language lets you import names unqualified, prefer namespaced references (e.g., `Module.foo` over `foo`). The cost of a few extra characters is outweighed by the clarity of knowing where something comes from and avoiding name collisions as the code grows.

7. **Handle sensitive data deliberately**: When handling data, consider whether any of it is sensitive and, if so, how it should be handled. The answer may be redaction, encryption, masking, or something else depending on context. Sensitive-data handling should be a deliberate, explicit decision rather than an accident.

8. **Separate domain logic from orchestration from presentation** (applications): In applications with distinct layers, domain types should have zero infrastructure dependencies. Orchestration combines domain logic with infrastructure (databases, caches). Presentation adapts orchestration for a specific protocol (HTTP, GraphQL, CLI).

9. **Design for changeability, not for predicted changes**: Make designs modular and replaceable so future needs can be accommodated, but don't add abstractions, extension points, or features for changes that haven't happened yet. The goal is a design that's easy to modify, not one that anticipates specific modifications.

10. **Type parameters in field types are not phantom**: When a type parameter appears only in stored field types (not in method signatures), it is still carrying type information through the pipeline. "Not mentioned in method bodies" does not mean "not needed." Before proposing to remove a type parameter, trace it to its terminal use — if it reaches a concrete type that depends on it, removing it loses compile-time guarantees.

11. **Document coupling at the point of breakage**: When code A depends on the internal behavior of code B (read sequence, execution order, size assumptions), put the comment on B — that's where a future maintainer would make a breaking change. Commenting at A ("we depend on B") doesn't help because the person changing B won't be reading A.

12. **Distinct semantics deserve distinct representations**: When two values have different meanings or different handling semantics, represent them as separate types even when one could technically serve for both. Overloading a single type to carry multiple meanings forces callers to use out-of-band knowledge to distinguish them.

13. **It is easier to give than take away**: When deciding whether to include something in an API (a callback, a parameter, a feature), lean toward omitting it. You can always add it later if needed, but removing it is a breaking change. Start minimal; expand based on demonstrated need.

14. **Don't patch around architectural problems**: When a remaining gap can't be fixed cleanly at the current layer, say so and stop. Don't write special-case workarounds for problems that need deeper fixes. If a fix requires assumptions about the internal structure of a different layer, it belongs in that layer. The bias toward producing a visible result ("I fixed this too!") leads to fragile code that papers over the real issue and makes the eventual proper fix harder to reason about.

15. **Trait/interface defaults only for universal invariants**: A default implementation should express behavior that's correct for every inheritor. If the correct behavior depends on which concrete type is implementing, make the method abstract at that level and push defaults down to intermediate traits or concrete types where a universal invariant actually holds. "Flip the default and add override-backs" hides state-dependent decisions behind inheritance semantics. Applies to any language with trait/interface/mixin defaults.
