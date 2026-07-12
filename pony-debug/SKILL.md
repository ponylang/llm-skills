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

Start by vetting the claim — a filed issue, or a problem you noticed yourself. Do not assume the problem exists, that any purported cause is true, or that its scope is properly defined.

## When to use the full protocol

This protocol is for non-trivial debugging — cases where you don't know the cause, or where your first guess could be wrong. If the cause is immediately obvious and verifiable in one step (a typo, a missing import), just fix it.

When the work started from a bug report and you plan the fix before writing it, checkpoints 1 through 6 come first. A plan built from the report has already set the scope at the reported symptom, and every check after that argues against a plan that is already settled.

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

**When the symptom is nondeterministic, orient at the scheduling layer first.** A test that fails on different runs, or passes on some platforms and not others, points at concurrency — scheduler contention, CPU count, actor scheduling, concurrent vs sequential execution — not at code logic. Tracing code paths to prove two versions are logically equivalent is the wrong level of analysis for a scheduling problem; a refactor that preserves logic can still change timing.

**When evidence refutes a hypothesis**: Form a NEW hypothesis from what the evidence actually shows. Do not shift the old hypothesis — "maybe it happens earlier" is the same hypothesis moved upstream. That's defending a theory, not following evidence.

**If stuck after 2-3 iterations without progress**: You are likely anchored to a bad hypothesis. Spawn a fresh-eyes subagent with the original problem, what you've tried, and your current hypothesis. The subagent's job is to verify your assumptions, generate alternative hypotheses, and report back. Act on its findings — don't dismiss them to defend your original theory.

**Exit condition**: You can explain all observed symptoms and have evidence supporting each link in the causal chain. Only then proceed to checkpoint 5.

### Checkpoint 5: Find where the cause reaches

You know why the bug happens. Before you decide what to change, find where else that cause reaches. You cannot pick where to fix until you know what the fix has to cover.

Bound the search by the mechanism checkpoint 4 gave you — the function, the field, the invariant that fails. That is what tells you when you are done, and it is why this is a directed search rather than a walk through the codebase.

Start where the bug was reported, and follow the cause outward. Often it simply reaches further than one place: the same bad value arriving at three call sites when only one of them got reported.

Sometimes it is worse than that. Two pieces of code are supposed to behave the same way, and nothing makes them. The difference between them is the defect, and the bugs it produces need not resemble each other at all — a crash in one, a hang in the other, a feature quietly absent from a third. What matters is that one thing produced them all. That divergence will keep producing bugs until you remove it.

When that is what you have, the second bug is not a second issue to file. It is one defect showing up twice — so long as the two really are supposed to behave the same. When they are not, you have two defects, and the test below tells you which case you are in.

Go and look. You cannot find those places from what you already know.

**Three signs a divergence has been papered over instead of removed.**

The first is in the fix you were about to write. It adds a field or a flag to one copy of something so that copy matches the other. Making two things agree by hand admits that nothing makes them agree.

The second is already in the code: a comment saying two things must change together. Take it seriously. A comment pairing two things that sit near each other — same type, same file, a few lines apart — is not documenting a coupling; `pony-comments` is explicit that a pairing with both ends in one file is not one. So go and look at what it is holding together. Often it is a defect somebody wrote down instead of removing: a value stored in a field where it should have been passed, two branches that should have been one. Writing it down is what stopped it looking like a bug. Sometimes it is a real invariant the code cannot express, and then it stays. You will not know which until you look. If what you find is the cause of the bug you came for, removing it is the fix, and checkpoint 6 is where you decide the place. If it is a tidy-up you happened to notice, restructuring it is a decision to raise, not one to fold into a bug fix.

The third is in the documentation. When one of two paths that should act alike is missing something, and the gap got written into the docs, the absence has been recorded as if it were a design choice.

**When it really is two defects.** The test is not whether the two places share code. It is whether they are supposed to behave the same. Two read loops that must respond identically to the same events are one defect, however little code they share. A missing check in a parser and a missing check in an unrelated request handler are two, however alike they look — fix the one you came for and record the other as a suspected issue (`pony-vet-suspected-issues`). Two defects is the answer that costs you less work right now, so be careful reaching for it. You have to be able to say why the two are *not* supposed to behave the same. If you can't, treat them as one defect.

Note what you saw anyway. The same mistake made independently twice is the best evidence you will get that the code permits a mistake it should make impossible. That is a design finding, worth more than either bug on its own. Raise it; don't quietly fix it.

That advice is for two defects. One defect in two places doesn't get raised and left alone — checkpoint 6 decides where it gets fixed.

**Artifact**: What you searched — the places the bad value can reach, and the code that ought to behave like the code the bug was reported in. How you found them, and what the cause does at each. Every place it reaches, the reported one among them. "Only the reported site" is a real answer, and it still has to name the places you ruled out.

### Checkpoint 6: Find where the fix belongs

Now pick the place to change. It has to cover every place checkpoint 5 found.

Name it. Ask whether any of those bugs could still happen by a route that change does not cover. If one could, that was the wrong place — either something upstream is still producing the bad value and your fix catches it late, or the same bad value reaches call sites your change does not touch. Move and ask again.

Sometimes no existing place covers everything. Two pieces of code that must agree, with nothing making them agree, have no shared place to fix, and that absence is the defect. Making them agree by hand, in each of them, is not the fix. Build the thing that makes them agree, and fix it there.

That is a larger change than the report asked for. Say so — in the plan, in the pull request, wherever the people who have to live with it will read it. Building it quietly is how a bug fix becomes a rewrite nobody agreed to.

If the cause reaches places you are not going to fix, that is a decision to raise, not a line to write here. If it cannot be fixed cleanly at any place you are able to change, say so and stop. Don't write the special case.

**Artifact**: The place you will change, and why nothing checkpoint 5 found still breaks once you have changed it. If you stopped instead, that is the artifact: the places you considered, why none of them can hold a clean fix, and what would have to change for one to exist.

### Checkpoint 7: Fix and verify

Fix the cause, in the place checkpoint 6 identified. Explain why this addresses the cause. A sleep, a retry, or a "just check again" that masks the problem is not a fix. Run the reproduction to confirm. For the other places checkpoint 5 found, build a check for each — and where you can't build one, say so rather than assume.

Read the fix you just wrote. Can you say why that code is there without mentioning the bug report? "The reader never returns an empty list" needs no report to make sense. "We check for an empty list here, because empty configs crashed" cannot be explained without one — the code is shaped like the report instead of like the program. If you need the report to explain the fix, you fixed the report. Go back to checkpoint 6.

**Artifact**: The fix, the rationale for why it addresses the cause, and evidence it resolves the issue.

## Honest use

The artifacts should reflect actual investigation, not be written retroactively after you've already decided on a cause. If you find yourself writing the characterization after you've already started coding a fix, you skipped the protocol — back up.

Checkpoint 5 is where this matters most. "I looked and found nothing" and "I did not look" produce the same sentence. Only one of them is true, and only you know which.
