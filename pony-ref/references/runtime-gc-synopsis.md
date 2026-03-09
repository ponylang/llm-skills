# Pony Runtime and Garbage Collection Synopsis

Reference for Pony's runtime architecture and garbage collection based on the
academic papers. The runtime uses two layered GC protocols: **ORCA** for object
collection and **MAC** for actor cycle collection.

## Source Papers

Listed in order of relevance to the current implementation:

1. **Clebsch et al., "Orca: GC and Type System Co-Design"** (OOPSLA 2017) —
   The most complete description of the object GC protocol. Covers
   ownership model, reference counting, immutability optimizations,
   barrier-free collection, and performance evaluation.

2. **Clebsch & Drossopoulou, "Fully Concurrent Garbage Collection of Actors
   on Many-Core Machines"** (2013) — Defines the MAC protocol for actor
   cycle collection. Conf-Ack protocol, causal messaging requirement,
   soundness proof.

3. **Clebsch, "Co-Designing a Type System and a Runtime"** (PhD thesis,
   2017) — Comprehensive treatment unifying ORCA, MAC, and runtime
   architecture. Covers pool allocator, page map, per-actor heaps,
   scheduler, and how the layers compose.

4. **Clebsch & Blessing, "Ownership and Reference Counting based Garbage
   Collection in the Actor World"** — Earlier formalization of the
   ownership model and reference counting protocol. Defines well-formedness
   conditions and collectability criteria.

## Architecture Overview

The runtime is layered bottom-up:

```
Pool Allocator        Thread-local, size-classed (2^5 to 2^20 bytes)
Page Map              Radix tree mapping addresses to chunk descriptors
Per-Actor Heaps       Size-classed chunks with allocation bitmaps
Message Queues        Lock-free MPSC queues, causal ordering
Scheduler             Work-stealing, one thread per core
Tracing GC            Mark-and-don't-sweep, per-actor, local only
Sharing GC (ORCA)     Reference counting on message send/receive
Actor GC (MAC)        Cycle detection for blocked actor groups
```

## ORCA: Object Garbage Collection

### Ownership Model

Every object is **owned** by the actor that allocated it, for its entire
lifetime. Only the owner can collect it. Other actors may hold references
(foreign references) but never take ownership.

### Reference Counts

Each shared object has four counts tracked across the system:

- **LRC** (Local Reference Count): The owner's count, stored in the owner's
  ORC map.
- **FRC** (Foreign Reference Count): Sum of reference counts held by all
  non-owning actors.
- **AMC** (Application Message Count): Number of in-flight application
  messages from which the object is reachable.
- **OMC** (Owner Message Count, called IDC in earlier work): Net weighted
  sum of pending INC and DEC messages in flight to the owner. An INC(ω, k)
  contributes +k; a DEC(ω, k) contributes -k. This is a weighted sum, not
  a count of messages.

### The Reference Count Invariant

The fundamental consistency equation:

```
LRC + OMC = FRC + AMC
```

This holds at quiescent points (start and end of atomically-executed
procedures). During concurrent execution it may be temporarily violated,
but the essential property — no premature collection — is preserved. It
means the owner's view of external interest
(LRC), adjusted for messages in flight (OMC), equals the actual external
interest (FRC + AMC). The invariant is maintained by the send/receive
protocol and causal message ordering.

### Protocol Operations

**Sending a reference to object ω in a message:**
- If sender is owner: increment LRC (one more external reference)
- If sender is not owner: decrement sender's FRC (transferring reference
  to message). If FRC would reach 0, first send INC to owner to acquire
  more weight.

**Receiving a reference to object ω from a message:**
- If receiver is owner: decrement LRC (reference has come home)
- If receiver is not owner: increment receiver's FRC (new foreign ref)

**INC message**: Owner increments LRC by the weight carried.
**DEC message**: Owner decrements LRC by the weight carried.

### Weighted Reference Counting

To reduce INC/DEC message traffic, ORCA uses weighted counts:

- When acquiring weight, an actor gets a batch (GCINC, typically 256)
  rather than incrementing by 1.
- Subsequent sends can decrement from the local weight without contacting
  the owner.
- INC messages are batched: the runtime accumulates reference count changes
  during a behavior and sends them together, not individually.
- An INC is only needed when an actor's local weight is exhausted.

### Object Collectability

An object ω is collectable when three **purely local** conditions hold at
the owner:

1. The owner has no reachable path to ω (not in heap traversal)
2. LRC = 0 (no outstanding external interest)
3. The owner is the one checking (trivially true)

When these hold, the reference count invariant guarantees FRC = 0 and
AMC = 0 — the object is globally unreachable.

### Object Cycles

Cycles of objects do not require special handling. Reference counts track
**actor interest** (how many actors care about an object), not pointer
topology. When all actors lose interest in a cycle of objects, each owner's
LRC drops to 0 independently, and each owner collects its own objects.

### Immutability Optimization

For `val` (immutable) objects:

- The entire reachable subgraph from an immutable root is immutable.
- A single reference count on the root protects the subgraph owned by the
  same actor. Objects in the immutable subgraph owned by a different actor
  need their own reference count roots.
- Tracing into immutable structures is skipped after first discovery.
- Passing immutable data between actors has near-zero GC overhead.

This optimization is significant in practice — sending `val` structures
avoids the tracing cost that dominates for large mutable graph transfers.

## Per-Actor Heap and Tracing GC

### Heap Structure

Each actor has a private heap with:

- Size-classed chunk lists (free and full) for small allocations
- Large allocation list for oversized objects
- Allocation bitmaps within chunks for slot tracking
- Used-memory counter and adaptive GC threshold

### Mark-and-Don't-Sweep

The local tracing collector runs between behaviors (when an actor finishes
processing a message). The algorithm:

1. Push actor's fields onto GC stack (these are the only roots — no stack
   frames exist between behaviors)
2. Mark all reachable objects via depth-first traversal using compiler-
   generated trace functions
3. Collect owned objects that are unmarked AND have LRC = 0
4. Send DEC messages for foreign objects no longer reachable

"Don't-sweep" means individual objects are not explicitly swept. The
allocation bitmap tracks which slots are live after marking; unmarked slots
are implicitly available for reuse. A post-mark pass iterates chunks to
find and free entirely empty ones, but there is no per-object sweep.

### Heap Closure and Owner Marking

If an object is in an actor's heap, the object's owner must also be
reachable from that actor (WF2 in the ownership-gc paper). During tracing,
when a foreign object is encountered, its owner is also marked. This
ensures actor lifetimes lower-bound the lifetimes of their objects.

### Finalization

Finalization runs between the mark and free phases. Finalizers execute on
unreachable objects before their memory is reclaimed. Pony guarantees
"safe" finalizers — a finalizer cannot revive an object (enforced
statically). This safety guarantee is part of the GC protocol's
correctness argument.

### GC Threshold

Collection triggers when heap usage exceeds a threshold:

- Initial threshold: configurable (default 2^14 bytes)
- After each cycle: threshold *= growth factor (default 2)
- Creates increasingly longer intervals between collections, amortizing
  overhead

### Compiler-Generated Trace Functions

The compiler synthesizes a trace function for each concrete type, encoding
how to traverse its fields based on their capabilities:

- `iso`, `trn`, `ref`, `box` fields: mark and recurse (mutable view)
- `val` fields: mark as immutable, do not recurse into substructure
- `tag` fields: mark object identity only, do not recurse (opaque)
- Primitive fields: skip (no pointers)

## MAC: Actor Cycle Collection

### The Problem

ORCA handles object collection but cannot collect **cycles of actors** that
reference each other with no external references. A group of actors all
blocked and only referenced by each other is dead but won't be collected by
reference counting alone.

### Actor Topology

Each actor maintains a local view of the actor reference graph:

- **Reference count (ρ)**: Number of incoming references from other actors
- **External set (ξ)**: Set of actors this actor holds references to
- **Blocked flag (β)**: Whether the actor is blocked (idle with empty queue
  after completing execution)

### Cycle Detector

A dedicated **cycle detector actor** (κ) monitors the system:

1. When an actor's queue empties, it sends **BLK(ι, ρ, ξ)** to κ with its
   topology snapshot.
2. When a blocked actor receives any message other than CNF (i.e., APP,
   INC, or DEC), it unblocks and sends **UNB(ι)** to κ.
3. κ maintains a **Perceived Topology (PT)** from accumulated BLK messages.
4. κ runs cycle detection on PT to find closed cycles — groups where all
   incoming references come from within the group.

### The Conf-Ack Protocol

A perceived cycle may not be a true cycle because κ's view may be stale.
The Conf-Ack protocol validates cycles without synchronization:

1. κ sends **CNF(τ)** (confirm with unique token) to each actor in the
   perceived cycle.
2. Each actor responds with **ACK(ι, τ)**.
3. **Critical rule**: CNF does not cause an actor to unblock. All other
   messages (APP, INC, DEC) do cause unblocking and trigger UNB.
4. If κ receives UNB from any actor in the cycle before all ACKs arrive,
   the perceived cycle is invalidated and cancelled.
5. If all actors ACK without any UNB, the cycle is confirmed as true.

**Why this works**: If an actor confirms, it means no APP, INC, or DEC
messages arrived between its BLK and the CNF (CNF itself doesn't unblock,
so other CNFs from concurrent cycle detection attempts are harmless).
Therefore its topology snapshot was still accurate. If all actors in the
cycle confirm, all snapshots were accurate simultaneously, proving the
cycle is real.

### Actor Collectability

An individual actor (not in a cycle) is collectable when:

1. Its reference count is 0 (no other actor references it)
2. Its message queue is empty

Cyclic groups of actors are collectable when confirmed by Conf-Ack.

When actors are collected, DEC messages are sent for actors in their
external sets that are *outside* the collected cycle (references within
the cycle are discarded), potentially triggering further collections.

## How ORCA and MAC Interact

ORCA's object reference counting creates **implicit actor-to-actor
references**. When actor A holds a foreign reference to an object owned by
actor B, A implicitly references B (because B must stay alive to own the
object). The actor-level external set used by MAC is derived from which
actors own objects that the current actor holds foreign references to. This
is why the heap closure property (WF2) matters: it ensures that object
ownership implies actor reachability, connecting the two protocols.

When ORCA's local tracing GC runs and drops foreign references (sending
DEC messages), this can change the actor-level topology that MAC monitors.
A DEC that reduces an actor's LRC to 0 may remove an implicit actor
reference, potentially enabling MAC to detect that the actor (or a cycle
containing it) is dead.

## Causal Message Ordering

### Requirement

Both ORCA and MAC require **causal message delivery**: if actor A sends
msg1 to B, then sends msg2 to C, and C (as a result of msg2) sends msg3
to B, then B must receive msg1 before msg3.

### Why It Matters

Without causal ordering, reference count updates can arrive out of order:

1. Actor A sends INC for object ω to owner B
2. Actor A sends ω in an APP message to C
3. C drops ω and sends DEC to B
4. If B receives DEC before INC, LRC goes negative — premature collection

Causal ordering guarantees INC arrives before any DEC that depends on it.

Formally, causal ordering preserves the **prefix invariant** (WF6 in the
ownership-gc paper): for any prefix of an actor's message queue, the LRC
adjusted by the weighted INC/DEC messages in that prefix never goes
negative. This is the invariant that prevents premature collection during
message processing.

### How It's Achieved

FIFO message queues with atomic enqueue naturally provide causal ordering
on a single node. Each actor has an MPSC (Multiple-Producer Single-Consumer)
queue. The atomic enqueue operation acts as a memory barrier making all
prior writes visible.

## Type System Enabling the Runtime

The type system's reference capability guarantees directly enable runtime
optimizations that would otherwise require synchronization:

| Guarantee | Enabled by | Runtime benefit |
|-----------|-----------|-----------------|
| No concurrent mutation | `iso` isolation, `val` immutability | No write barriers |
| No concurrent read during write | Deny-properties matrix | No read barriers |
| Safe zero-copy messaging | `iso`, `val`, `tag` are sendable | Objects passed by reference, not copied |
| Per-actor GC without coordination | Exclusive mutability (I1) | No stop-the-world |
| Deep immutability optimization | `val` is deeply, persistently immutable | Single RC for immutable subgraphs |
| No stack maps needed | GC runs between behaviors only | No safepoints, no stack crawling |
| Barrier-free tracing | Race-freedom guarantee | Trace functions safe without synchronization |

### Five Invariants ORCA Depends On

1. **I1 (Exclusive Mutability)**: If an actor may write to an object, no
   other actor can read or write it.
2. **I2 (Persistent Deep Immutability)**: Immutable objects remain immutable
   and only reference immutable or opaque objects.
3. **I3 (Live Objects Protected at Owner)**: Any live object has positive
   LRC at its owner.
4. **I4 (Foreign Objects Protected)**: Any object reachable from a foreign
   actor has positive FRC at that actor.
5. **I5 (Reference Count Consistency)**: LRC + OMC = FRC + AMC.

## Scheduler

### Work-Stealing Design

- One scheduler thread per core, pinned
- Each thread has a thread-local pool allocator (no contention)
- Actors are scheduled onto threads; idle threads steal from neighbors
- Each actor gets an execution quantum before being rescheduled

### Integration with MAC

- BLK messages are sent when an actor is genuinely idle (queue empty), not
  merely when its quantum expires.
- The cycle detector is a special non-application actor processed by the
  scheduler.

## Pool Allocator

- Thread-local size-classed free lists (LIFO for cache locality)
- Global size-classed free list (atomic CAS, prevents starvation)
- Thread-local free block list (insert-sorted by size for large allocs)
- Cache-line aligned; huge page support when available
- No allocation size stored in blocks (compiler knows sizes)

## Performance Characteristics

From the ORCA paper's evaluation:

- **Scalability**: Near-linear scaling from 4 to 64 cores
- **No stop-the-world**: Per-actor GC keeps pause times per-actor, not
  system-wide
- **Low jitter**: Small, bounded response time variance compared to
  stop-the-world collectors
- **Immutable optimization impact**: Sending `val` structures has near-zero
  overhead vs. 21% overhead for large mutable graph transfers
- **Message overhead**: Most benchmarks send no INC messages (good weight
  allocation); DEC messages ~10x fewer than GC cycles
- **Weighted RC**: Single ACQUIRE message replaces hundreds of individual
  INC messages

## Soundness Results

- **MAC Soundness**: Only truly dead actors are collected (proved via
  Conf-Ack protocol correctness)
- **MAC Completeness**: All dead actors are eventually collected (requires
  guaranteed message delivery)
- **ORCA Object Safety**: Objects are collected only when globally
  unreachable (follows from reference count invariant + collectability
  criteria)
- **Data-race freedom**: GC operations never race with application code
  (follows from type system guarantee I1)

## Robustness

- **Cycle detector failure**: Cycles won't be collected, but no live actors
  are falsely collected (soundness preserved, completeness lost)
- **Actor failure**: Affects completeness, not soundness
- **Message loss**: INC/UNB loss could affect soundness, but Pony's
  actor model guarantees delivery on a single node

## Implementation Divergences from Papers

The papers represent a snapshot in time. The ponyc runtime has continued
evolving. The core ORCA and MAC algorithms are faithfully preserved, but
significant pragmatic changes have been made. When reasoning about current
runtime behavior, use this section to correct paper-era assumptions.

Source: comparison against `ponyc/src/libponyrt/` (verified March 2026).

### Cycle Detector Protocol Changes

**BLK sends deltas, not full external sets.** The papers describe
BLK(ι, ρ, ξ) carrying the actor's reference count and complete external
set. The implementation sends a `deltamap_t` — only the changes since the
last BLK message. The cycle detector accumulates deltas via `apply_delta()`
to maintain its view. This reduces message size but means the cycle
detector must maintain cumulative state.
(`gc/cycle.c`: `block_msg_t`, `apply_delta()`)

**Actors do not register at creation.** The papers describe actors
informing the cycle detector of their existence at creation. The
implementation abandoned this to reduce message traffic — actors only
contact the cycle detector when they become blocked.
(`gc/cycle.c` comment block, lines 86–93)

**Cycle detector actively polls actors.** Beyond the paper's purely
self-reporting model, the implementation adds `ACTORMSG_ISBLOCKED`
messages: the cycle detector proactively asks known actors if they're
blocked. This handles actors discovered through other actors' deltas
rather than self-reporting. Rate-limited to max(total/10, 1000) actors
per invocation.
(`gc/cycle.c`: `check_blocked()`)

**UNB is gated on BLOCKED_SENT flag.** The paper says any non-CNF message
causes unblocking and triggers UNB. The implementation only sends UNB if
`ACTOR_FLAG_BLOCKED_SENT` is set. If the actor was blocked but hadn't yet
reported to the cycle detector, it simply clears its local flag — no UNB
needed since the cycle detector doesn't know about it.
(`actor/actor.c`: `maybe_unblock()`)

**Cycle detector runs on scheduler 0 only, time-gated.** Rather than being
scheduled like a normal actor, the cycle detector is triggered by scheduler
thread 0 on a configurable time interval. Messages use an inject queue
that bypasses normal scheduling.
(`gc/cycle.c`: `ponyint_cycle_check_blocked()`)

### Fast-Reap Optimizations (Not in Papers)

**rc=0 actors are reaped immediately by the cycle detector.** When an
actor sends BLK with rc=0, the cycle detector destroys it directly without
running cycle detection. These "zombie actors" have no incoming references
and are trivially dead.
(`gc/cycle.c`: `block()` fast path at rc == 0)

**Orphaned actors self-delete without cycle detector involvement.** The
compiler can determine at actor creation time whether any references to
the actor will be held. Orphaned actors (rc never above 0) skip the cycle
detector entirely and self-delete when their queue empties.
(`actor/actor.c`: `pony_create()` orphaned parameter,
`ACTOR_FLAG_RC_OVER_ZERO_SEEN`)

### GC Threshold Is Not Simply Multiplicative

The papers describe GC threshold growing as `threshold *= factor`. The
implementation has additional logic: if more than 100 actor references
were deleted in a GC cycle, the threshold is held at its current value
(not allowed to grow). This causes more frequent GC for actors with high
actor-reference churn.
(`mem/heap.c`: `ponyint_heap_endgc()`, `ACTOR_REFERENCES_DELETED_THRESHOLD`)

### Backpressure / Muting (Not in Papers)

The implementation adds a backpressure system absent from the papers:

- **Overloaded actors**: If an actor hits its message batch limit without
  emptying its queue, it's marked overloaded.
- **Muting**: Actors that send to an overloaded/under-pressure actor are
  "muted" — removed from scheduling until the receiver recovers.
- **Under pressure**: FFI code can signal external backpressure via
  `pony_apply_backpressure()`.

This prevents unbounded message queue growth and memory exhaustion.
(`actor/actor.c`: `maybe_mark_should_mute()`, `mute_actor()`)

### Dynamic Scheduler Scaling (Not in Papers)

The papers assume a static one-thread-per-core model. The implementation
supports dynamically suspending and resuming scheduler threads based on
workload. Idle threads can sleep to reduce CPU usage, waking when new
work arrives. Configurable via `--ponynoscale` (disable) and
`--ponyminthreads` (floor).
(`sched/scheduler.c`: `perhaps_suspend_scheduler()`,
`wake_suspended_threads()`)

### Thread Pinning Is Optional

The papers and synopsis describe threads pinned to cores. In the
implementation, CPU affinity is configurable and can be disabled via
`--ponynopin`.

### Additional Trace Optimization

The compiler provides a `might_reference_actor` flag on each type. When
tracing immutable objects, if the type cannot transitively reference an
actor, tracing is skipped entirely — even the owner-marking step. This
optimization is not described in the papers.
(`pony.h`: `pony_type_t.might_reference_actor`)
