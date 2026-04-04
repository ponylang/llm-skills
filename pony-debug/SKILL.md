---
name: pony-debug
description: Structured debugging protocol with checkpoints. Load when debugging non-trivial issues — before forming any hypothesis about the cause.
disable-model-invocation: false
---

# Debugging Protocol

A structured protocol for debugging non-trivial issues. Each checkpoint requires a visible artifact before proceeding to the next step.

## Overarching principle

Don't assert a cause. State hypotheses explicitly. Prove the execution path with evidence. When evidence contradicts your hypothesis, discard it entirely and form a new one from what the evidence actually shows. Don't shift the same hypothesis upstream — that's defending a theory, not following the evidence.

A hypothesis is not knowledge. If you can test it, test it. This protocol makes that concrete for debugging sessions.

## When to use the full protocol

This protocol is for non-trivial debugging — cases where you don't know the cause, or where your first guess could be wrong. If the cause is immediately obvious and verifiable in one step (a typo, a missing import), just fix it.

## Protocol

### Checkpoint 1: Characterize the failure

What's broken? State the expected behavior vs observed behavior. What invariant is violated? Be precise about symptoms — error message, wrong output, crash, hang, intermittent behavior.

**Artifact**: Written failure characterization.

### Checkpoint 2: Gather context

Read the relevant code paths. Understand the execution context, what state is involved, what the entry points are. For intermittent failures, note the reproduction rate and what conditions affect it.

**Artifact**: Summary of relevant code paths and state involved.

### Checkpoint 3: Minimal reproduction

Build a minimal reproduction — the smallest, simplest case that triggers the failure. Don't just re-run the failing test suite. Strip away everything that isn't necessary to trigger the bug. A minimal reproduction has less surface area, simpler generated code, fewer interacting components, and fewer possible explanations. This makes every subsequent checkpoint easier.

For intermittent failures, try to increase the rate — stress test in a tight loop, reduce timing margins, run on constrained resources. If reproduction isn't achievable, state why explicitly.

**Artifact**: A minimal reproduction with steps/command and evidence it triggers the failure. If reproduction isn't achievable, an explicit statement of why and what alternative strategy you're using instead.

### Checkpoint 4: Investigation loop

This is the core of debugging. It's an OODA loop — observe, orient, decide, act — not a linear sequence. You rarely understand the full picture at the start. The goal is to narrow the problem space iteratively until you can explain all symptoms.

**Each iteration:**

1. **Orient**: State a hypothesis about some subset of the problem. It doesn't need to explain everything yet — but be explicit about what it covers and what remains unexplained. "I think [cause] because [evidence]. This would explain [symptoms A and B] but not [symptom C]."

2. **Decide**: Design an experiment that would confirm or refute this hypothesis. What would you expect to see if it's right? What would you expect if it's wrong?

3. **Act**: Run the experiment — instrument the code, add logging or assertions, run the reproduction. Report what was observed.

4. **Observe**: What did the evidence show? Did it confirm, refute, or reveal something unexpected? Update your understanding of the problem space.

Then loop. Each iteration should narrow the space — ruling out possibilities, confirming parts of the causal chain, surfacing new information. Keep going until your hypothesis accounts for all observed symptoms.

**Artifact per iteration**: The hypothesis, the experiment, what was observed, and what was learned. Accumulate these — the trail of evidence is how you build toward a complete explanation.

**When evidence refutes a hypothesis**: Form a NEW hypothesis from what the evidence actually shows. Do not shift the old hypothesis — "maybe it happens earlier" is the same hypothesis moved upstream. That's defending a theory, not following evidence.

**If stuck after 2-3 iterations without progress**: You are likely anchored to a bad hypothesis. Spawn a fresh-eyes subagent with the original problem, what you've tried, and your current hypothesis. The subagent's job is to verify your assumptions, generate alternative hypotheses, and report back. Act on its findings — don't dismiss them to defend your original theory.

**Exit condition**: You can explain all observed symptoms and have evidence supporting each link in the causal chain. Only then proceed to the fix.

### Checkpoint 5: Fix and verify

Fix the root cause, not the symptom. Explain why this addresses the root cause. A sleep, a retry, or a "just check again" that masks the problem is not a fix. Run the reproduction to confirm.

**Artifact**: The fix, the rationale for why it addresses the root cause, and evidence it resolves the issue.

## Honest use

The artifacts should reflect actual investigation, not be written retroactively after you've already decided on a cause. If you find yourself writing the characterization after you've already started coding a fix, you skipped the protocol — back up.
