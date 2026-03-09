# Pony Type System Synopsis

Reference for the Pony type system based on the academic papers. Pony currently
uses **the Steed model** (PonyG), formalized by George Steed in "A Principled
Design of Capabilities in Pony" (2016). The Steed model supersedes the original
PonyS model from Clebsch et al. ("Deny Capabilities for Safe, Fast Actors",
2015).

## Source Papers

The type system is defined across several papers. Listed in order of relevance
to the current implementation:

1. **George Steed, "A Principled Design of Capabilities in Pony"** (2016) —
   The active formalization (PonyG). Introduces extracting viewpoint
   adaptation, active/passive temporaries, uniform well-formedness, and
   Prolog-verified lemmas. Found a data-race bug in intersection types.

2. **Clebsch et al., "Deny Capabilities for Safe, Fast Actors"** (2015) —
   The foundational paper (PonyS). Introduced the deny-properties matrix,
   all six capabilities, viewpoint adaptation, safe-to-write, aliasing,
   recovery, and the core safety invariants.

3. **Paul Lietar, "Formalising Generics for Pony"** (2017) — Extends PonyG
   with generics (PonyPL). Key technique: partial reification. Found
   compiler unsoundness bugs. Soundness proof was not completed.

4. **Sylvan Clebsch, "Co-Designing a Type System and a Runtime"** (PhD
   thesis, 2017) — Comprehensive formalization covering type system + ORCA
   + MAC. Introduces deep viewpoint adaptation. Proves preservation and
   data-race freedom.

5. **Clebsch et al., "Orca: GC and Type System Co-Design"** (OOPSLA 2017)
   — Shows how type system guarantees enable per-actor GC without
   stop-the-world, read/write barriers, or synchronization.

Papers 6-9 (MAC, OGC/Pony-ORCA, "A String of Ponies") cover runtime/GC and
have no type system formalism beyond relying on the guarantees above.

## The Six Reference Capabilities

Capabilities describe what other aliases are **denied**, not what a reference
can do. They are derived from a deny-properties matrix:

```
                    | Deny global    | Deny global  | Allow all
                    | read/write     | write only   | global
--------------------+----------------+--------------+----------
Deny local r/w      | iso (isolated) |              |
Deny local write    | trn (transition)| val (value) |
Allow all local     | ref (reference)| box          | tag
```

Capabilities on the diagonal (`iso`, `val`, `tag`) are **sendable** — safe to
pass between actors — because their local and global deny properties are the
same.

### What each capability means

- **`iso`**: The only stable readable/writable alias in the entire program.
  Denies all local and global aliases except `tag`. Can read, write, and be
  sent to other actors (via destructive read).
- **`trn`**: Write-unique. Only one mutable alias exists, but other aliases in
  the same actor may read. Denies global read/write and local write aliases.
  Can transition to `val` for sharing.
- **`ref`**: Mutable, freely aliasable within the same actor. Denies global
  read/write aliases. Cannot be sent to other actors.
- **`val`**: Deeply and persistently immutable. Denies all local and global
  write aliases. Freely sendable and shareable. Once `val`, always `val`.
- **`box`**: Read-only from this reference's perspective, but the underlying
  object may be mutable through another alias in the same actor. Denies
  global write aliases only.
- **`tag`**: Opaque. No deny properties. Cannot read or write. Can compare
  identity and call behaviours (async methods). Used to type actors from
  outside.

### Actor typing

Actors see themselves as `ref` (can read/write own fields). All other actors
see them as `tag` (can only call behaviours).

## Subtyping

The capability subtyping lattice (with ephemeral modifiers):

```
        iso^  (top — subtypes to everything)
       /    \
     iso    trn^
      |    / | \
      |  trn ref val
      |    \  |  /
      |     box
       \    /
        tag  (bottom)
```

Where `^` denotes ephemeral (one alias removed). Direct subtyping
relationships:

- `iso^ <: {iso, trn^}`
- `trn^ <: {trn, ref, val}`
- `{trn, ref, val} <: box`
- `{iso, box} <: tag`

Subtyping is reflexive and transitive.

## Ephemeral Modifiers

Two meaningful ephemeral capabilities exist:

- **`iso^`** (written `iso-` in Steed): Zero stable aliases in the entire
  program. Returned by destructive reads and field assignments. In the formal
  model, constructors return `ref` (recovery is needed to get `iso^`); the
  compiler may perform automatic recovery. Subtypes to everything.
- **`trn^`** (written `trn-` in Steed): Zero stable mutable aliases. Subtypes
  to `trn`, `ref`, and `val`.

For `ref`, `val`, `box`, `tag`: the ephemeral form is equivalent to the
non-ephemeral form (`ref^ ≡ ref`, etc.).

## Aliasing (`+`)

When creating a new alias, the alias operator gives the minimum compatible
capability:

```
+iso  = tag    (iso denies all local aliases)
+trn  = box    (trn denies local write aliases)
+ref  = ref
+val  = val
+box  = box
+tag  = tag
+iso^ = iso    (was one-removed, aliasing restores it)
+trn^ = trn
```

## Unaliasing (`-`)

When removing an alias (destructive read), the unalias operator strengthens:

```
-iso = iso^
-trn = trn^
-ref = ref     (ref^ ≡ ref)
-val = val
-box = box
-tag = tag
```

## Compatibility

### Local compatibility (`~l`)

Can two capabilities coexist as aliases within the same actor?

```
         iso  trn  ref  val  box  tag
iso                                ✓
trn                           ✓   ✓
ref                ✓         ✓   ✓
val                     ✓   ✓   ✓
box            ✓   ✓   ✓   ✓   ✓
tag       ✓   ✓   ✓   ✓   ✓   ✓
```

### Global compatibility (`~g`)

Can two capabilities coexist as aliases across different actors?

```
         iso  trn  ref  val  box  tag
iso                                ✓
trn                                ✓
ref                                ✓
val                     ✓   ✓   ✓
box                     ✓   ✓   ✓
tag       ✓   ✓   ✓   ✓   ✓   ✓
```

Key insight: any mutable capability (`iso`, `trn`, `ref`) is only globally
compatible with `tag`.

## Viewpoint Adaptation

### Non-extracting viewpoint adaptation (`λ.κ`)

The capability obtained when **reading** a field of capability `κ` through an
origin of capability `λ`. This is the Steed model's version (PonyG), which is
more permissive than PonyS for ephemeral origins:

```
λ.κ      iso    trn    ref    val    box    tag
iso^    iso^   iso^   iso^   val    val    tag
iso     iso    iso    iso    val    tag    tag
trn^    iso^   trn^   trn^   val    val    tag
trn     iso    trn    trn    val    box    tag
ref     iso    trn    ref    val    box    tag
val     val    val    val    val    val    tag
box     tag    box    box    val    box    tag
tag      ⊥      ⊥      ⊥     ⊥      ⊥      ⊥
```

Cannot read through `tag` (undefined/bottom).

### Extracting viewpoint adaptation (`λ▷κ`)

The capability obtained when **destructively reading** (overwriting) a field of
capability `κ` through an origin of capability `λ`. This operator is **novel
to the Steed model** — PonyS used `-(λ.κ)` which was overly restrictive.

```
λ▷κ      iso    trn    ref    val    box    tag
iso^    iso^   iso^   iso^   val    val    tag
iso     iso^   val    tag    val    tag    tag
trn^    iso^   trn^   trn^   val    val    tag
trn     iso^   val    box    val    box    tag
ref     iso^   trn^   ref    val    box    tag
```

Only defined for writable origins (`iso^`, `iso`, `trn^`, `trn`, `ref`).
`val`, `box`, `tag` cannot be written to, so extracting through them is
undefined.

Key differences from non-extracting: extracting through `iso` on a `trn` field
gives `val` (not `iso`), and on a `ref` field gives `tag` (not `iso`).
Extracting through `trn` on a `trn` field gives `val` (not `trn`).

### Well-formedness requirements (Steed)

Non-extracting viewpoint adaptation must satisfy 5 requirements (R1-R5):

- **R1**: If either `λ` or `κ` is immutable, so is `λ.κ`.
- **R2**: Field global compatibility is preserved: `κ ~g κ'` implies
  `+(λ.κ) ~g κ'`.
- **R3**: Local compatibility is preserved through the operator.
- **R4**: Object global compatibility is preserved.
- **R5**: Sendable capabilities preserve global compatibility under subtyping.

These requirements are exhaustively verified by Prolog.

## Safe-to-Write (`λ/κ`)

Determines which capability `κ` values can be written into a field through an
origin of capability `λ`:

```
λ/κ     iso   trn   ref   val   box   tag
iso^     ✓     ✓     ✓     ✓     ✓     ✓
iso      ✓                 ✓           ✓
trn^     ✓     ✓     ✓     ✓     ✓     ✓
trn      ✓     ✓           ✓           ✓
ref      ✓     ✓     ✓     ✓     ✓     ✓
```

`iso^` and `trn^` allow writing anything because the origin will never be seen
again (the alias is consumed). `iso` only allows sendable values (`iso`,
`val`, `tag`). `trn` allows `iso`, `trn`, `val`, `tag` but not `ref` (would
break write uniqueness). `ref` allows everything. `val`, `box`, `tag` are not
writable origins.

## Recovery

A `recover` block restricts access to only sendable variables from the
enclosing scope, allowing capability lifting:

```
R(iso) = iso^     R(val) = val
R(trn) = iso^     R(box) = val
R(ref) = iso^     R(tag) = tag
```

Any mutable capability recovers to `iso^`. Any immutable capability recovers
to `val`. `tag` stays `tag`.

## Sendable Types

Only capabilities where local and global deny properties are the same can be
sent between actors: `{iso, val, tag}`. Behaviour arguments must be sendable.

## Active and Passive Temporaries (Steed)

A key Steed innovation: at most one **active temporary** exists per actor at
any time. Active temporaries are the result of a field read or write currently
being evaluated. They retain their full (possibly unique) capability.

All other temporaries are **passive** — they have been aliased and hold aliased
capabilities. This distinction simplifies well-formedness reasoning.

## Well-Formed Visibility (WFV) and Well-Formed Temporaries (WFT)

The core safety invariants. In the Steed model, heap well-formedness requires
both WFV and WFT to hold.

### WFV (Steed model — 3 conditions)

1. **WFV.1 (Global consistency)**: Paths from different actors to the same
   object must have globally compatible capabilities.
2. **WFV.2 (Local consistency)**: Non-active extended paths from the same
   actor to the same object must have either interfering paths or locally
   compatible capabilities (after aliasing one of them).
3. **WFV.3 (Active temporary consistency)**: An active temporary with
   capability `λ'` and any other extended path with capability `λ` to the
   same object must satisfy: `+(+λ') ~l λ` and `+λ ~l +λ'`. Interference
   cannot occur by the structure of active temporaries, so only the
   compatibility conditions apply.

Note: PonyS had 4 WFV conditions including containment and unique temporary
properties. The Steed model's uniform path-based approach with extended paths
and interfering paths subsumes these into 3 simpler conditions.

### WFT (Well-Formed Temporaries)

At most one active temporary exists per actor at any time. Active temporaries
are the ones at the focus of execution (field read/write). All other
temporaries are passive and hold aliased capabilities.

## Soundness Results

- **Data-race freedom** (Theorem 1 in Clebsch 2015, Theorem 4.1 in Clebsch
  2017): If two actors simultaneously access the same object and one is
  writing, it's a contradiction — the type system prevents this.
- **Preservation** (Theorem 2 / 4.2): Well-formed heaps are preserved through
  all execution steps (field read, local/field assignment, method call/return,
  message passing).
- **Atomicity of behaviours**: Because readable references stay readable
  (capabilities don't change at runtime), behaviours are logically atomic —
  stronger than mere data-race freedom.

## Generics (Lietar 2017)

### Capability Constraints

Type variables have capability constraints bounding which capabilities they
can be instantiated with:

- `#any` = {iso, trn, ref, val, box, tag}
- `#read` = {ref, val, box}
- `#send` = {iso, val, tag}
- `#share` = {val, tag}
- `#alias` = {ref, val, box, tag}
- `#any^` = {iso^, trn^, ref, val, box, tag}
- `#send^` = {iso^, val, tag}

### Partial Reification

The key technique for type-checking generics. Rather than treating type
variables as opaque, partial reification assigns concrete capabilities from
within bounds and checks all possible instantiations exhaustively. A type
expression is valid only if it reduces successfully under every well-formed
partial reification.

### Known Issues Found

- Unsoundness in compiler's handling of unaliased viewpoint-adapted types:
  `val->(X!)` unaliased incorrectly.
- Type arguments inside bounds should be regular types, not bounds (fixed in
  compiler v0.13.2).

## Steed vs. PonyS: Key Differences

| Aspect | PonyS (Clebsch 2015) | PonyG/Steed (2016) |
|--------|---------------------|--------------------|
| Viewpoint adaptation | Single operator for read and write | Separate non-extracting and extracting operators |
| Extracting reads | Used `-(λ.κ)` (overly restrictive) | Dedicated operator with its own well-formedness requirements |
| Ephemeral modifiers | Part of the type, not capability | Part of the capability itself |
| Well-formedness | Special cases for iso/trn | Uniform path-based definition using extended paths |
| Temporaries | No active/passive distinction | Active (at most one) vs. passive distinction |
| Subtyping | `iso ≤ trn`, `trn ≤ {ref, val}` held directly (broke lemmas like `κ ≤ κ' → κ ~l +κ'`) | These moved to ephemeral-only: `iso^ ≤ trn^`, `trn^ ≤ {trn, ref, val}`; non-ephemeral iso/trn only subtype to tag/box respectively (lemmas hold cleanly) |
| Verification | Paper proofs only | Prolog exhaustive verification of capability lemmas |
| Intersection types | Not covered (had a hidden bug) | Covered; data-race bug discovered and addressed |

## Deep Viewpoint Adaptation

Introduced in the PonyS paper (Clebsch et al. 2015, Figure 4) and reused in
the Clebsch PhD thesis (2017, Figure 4.8). The deep viewpoint adaptation
operator (`κ▿κ'`) is used in the formalization of path visibility. Standard
viewpoint adaptation (`κ.κ'`) handles a single field read. Deep viewpoint
adaptation handles paths of arbitrary depth through fields — the capability
obtained by following a chain of field reads.

Definition:
- If κ is writable (iso, trn, ref): `κ▿κ' = κ'` (deep mutability — the
  field's own capability is preserved)
- If either κ = val or κ' = val: `κ▿κ' = val` (deep immutability)
- If κ = box and κ' ∉ {iso, val, tag}: `κ▿κ' = box`
- Otherwise: `κ▿κ' = tag`

Key properties:
- Deep adaptation is no more permissive than shallow: `κ▿κ' ≤ κ.κ'`
- Subtyping, local compatibility, and global compatibility are preserved
  through deep adaptation

This operator is used in the WFV definitions for reasoning about heap
visibility along multi-step paths. It is conceptually subsumed by the Steed
model's extended paths approach.

## Co-Design with Runtime

The type system's guarantees directly enable runtime optimizations:

- **No stop-the-world GC**: Per-actor GC is safe because the type system
  guarantees no shared mutable state across actors.
- **Zero-copy messaging**: `iso` and `val` can be passed between actors
  without copying.
- **No read/write barriers**: Data-race freedom means no concurrent writes to
  readable data.
- **Deep immutability optimization**: `val` is deeply and persistently
  immutable, so immutable subgraphs need only a single reference count on
  the root.
- **Causal messaging**: Required for GC correctness; the type system's
  sendable type restrictions interact with the runtime's message ordering
  guarantees.
