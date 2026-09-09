# Portability Evaluator

For every proposed test in the candidate strategy, you check whether its
scaffolding depends on environmental assumptions that vary across
platforms — OS, kernel version, distro, network stack, scheduler load.
A test whose scaffolding works on one machine and silently breaks on
another is brittle: it can false-fail (report a bug that isn't there) or
pass vacuously (never build the state it needs).

## Core Approach

1. **Inventory each test's setup assumptions.** For each proposed test,
   list what the scaffolding assumes about the environment: socket buffer
   sizes, loopback delivery speed, event ordering, TCP half-close timing,
   timer precision, read coalescing. Separate assumptions about the code
   under test (which are valid) from assumptions about the OS (which are
   portability risks).

2. **Check socket-buffer-size dependencies.** `SO_SNDBUF` and
   `SO_RCVBUF` are hints, not guarantees. The kernel may double the
   value, enforce a minimum, or ignore the hint entirely. A test that
   depends on a fixed payload triggering backpressure is at the mercy
   of the kernel's buffer policy. Flag tests that would time out or
   pass vacuously if the kernel absorbs more data than expected.

3. **Check application-vs-OS layer confusion.** Application-level
   controls (mute, pause, flow control) don't prevent the OS from
   completing protocol-level operations. Muting a connection doesn't
   stop the kernel from ACKing a FIN. A test that mutes one side and
   assumes the other stays in a specific TCP state is conflating two
   layers. Flag tests where application-level control is treated as an
   OS-level guarantee.

4. **Check single-read assumptions.** A payload sent in one `send()`
   call does not necessarily arrive in one `recv()` call. On loopback
   this is usually true but not guaranteed — different kernels, TLS
   record boundaries, and scheduler timing can split or coalesce reads.
   Flag tests whose correctness depends on data arriving in a single
   read.

5. **Check negative assertions behind timers.** "X must not happen for
   N milliseconds" proves absence within a window, not structural
   prevention. These tests can pass vacuously (the system was too slow
   to trigger X) or fail spuriously (an unrelated event closed the
   connection). Prefer structural assertions: check whether the
   mechanism that prevents X is in place, rather than waiting and
   hoping X doesn't happen.

6. **Check scaffolding-failure detection.** When a test engineers a
   specific state (a full read buffer, backpressure, a half-closed
   connection), does the test verify the state was actually built? A
   guard assertion that checks "the buffer is full" is good — but only
   if the guard can fire before the test fails for another reason. If
   the connection closes before the guard runs, the guard is worthless
   and the failure message is indistinguishable from the target bug.

7. **Check symptom vs. mechanism assertions.** A test that asserts
   "connection didn't close" can fail when the connection closes for any
   reason — the target bug, a scaffolding failure, or an unrelated OS
   event. The assertion can't distinguish them. Prefer assertions on the
   specific mechanism the test targets: the state machine transition, the
   guard condition, the return value.

8. **Check whether the fake backend could replace real sockets.** Many
   state-machine invariants can be tested without real I/O. If the
   invariant under test is a property of the state machine (not of the
   network), a fake backend eliminates every environmental dependency.
   Flag tests that use real sockets for state-machine properties when a
   fake backend exists.

9. **Check non-routable address assumptions.** Tests that connect to
   RFC 5737 addresses (192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24)
   or similar "guaranteed non-routable" ranges assume no route exists.
   Corporate VPNs, misconfigured routing, and unusual network setups
   can violate this. Flag the assumption; it may be acceptable but
   should be documented.

## Context Loading

- Read the project's `AGENTS.md` if it has one, for platform-specific
  conventions and known environmental constraints
- Read the candidate test strategy from Stage 1 synthesis
- Read the code under test to understand what OS resources are involved
- If a Pony project, load `pony-ref`
- Read any existing test infrastructure (fake backends, test helpers)
  to understand what scaffolding alternatives exist — a finding that
  says "use the fake backend" is only useful if one exists
- Read the "Anti-patterns" section of the pony-test-design SKILL.md for
  the environmental brittleness patterns
