---
name: pony-debug
description: Structured debugging protocol with checkpoints. Load when debugging non-trivial issues — before forming any hypothesis about the cause.
disable-model-invocation: false
---

# Debugging Protocol

A structured protocol for debugging non-trivial issues. Each checkpoint requires a visible artifact before proceeding to the next step.

## Overarching principle

Don't assert a cause without evidence. State hypotheses explicitly. Establish the execution path with measurements, not code reading alone. When established evidence contradicts your hypothesis, discard it and form a new one from what the evidence shows. If the contradiction depends on an unverified assumption about a measurement, verify that assumption before deciding. Don't shift the same hypothesis upstream — that's defending a theory, not following the evidence.

A hypothesis is not knowledge. If you can test it, test it. This protocol makes that concrete for debugging sessions.

Start by vetting the claim — a filed issue, or a problem you noticed yourself. Do not assume the problem exists, that any purported cause is true, or that its scope is properly defined.

## When to use the full protocol

This protocol is for non-trivial debugging — cases where you don't know the cause, or where your first guess could be wrong. If the cause is immediately obvious and verifiable in one step (a typo, a missing import), just fix it.

When the work started from a bug report and you plan the fix before writing it, checkpoints 1 through 7 come first. A plan built from the report has already set the scope at the reported symptom, and every check after that argues against a plan that is already settled.

## Protocol

### Checkpoint 1: Characterize the failure

What's broken? State the expected behavior vs observed behavior. What invariant is violated? Be precise about symptoms — error message, wrong output, crash, hang, intermittent behavior.

**Artifact**: Written failure characterization.

### Checkpoint 2: Gather context

Gather observations of the failure and their sources before interpreting them. Record the version, configuration, workload, and environment for each relevant artifact or measurement. Compare with successful runs, unaffected cases, or another failure mode. Record known differences before treating those cases as controls; a difference in configuration or workload may explain the result. Check whether a control shares the suspected defect before relying on the comparison.

Read the relevant code paths to understand the execution context, state, and entry points, and to locate useful measurements. For intermittent failures, note the reproduction rate and what conditions affect it. Keep observations separate from explanations inferred from the code.

**Artifact**: Observations with sources and context, available controls and their known differences, and a summary of relevant code paths and state involved.

### Checkpoint 3: Minimal reproduction

Build a minimal reproduction — the smallest, simplest case that triggers the failure. Don't just re-run the failing test suite. Compare its measurements with the incident evidence: the same error or visible symptom can result from a different mechanism. Preserve the observations that distinguish the incident from those alternatives as you reduce the case. A minimal reproduction has less surface area, simpler generated code, fewer interacting components, and fewer possible explanations. This makes every subsequent checkpoint easier.

For intermittent failures, try to increase the rate — stress test in a tight loop, reduce timing margins, run on constrained resources. Record how those changes affect the distinguishing measurements. Until the comparison matches, or when incident evidence is unavailable, call it a candidate reproduction and state what remains unverified. If reproduction isn't achievable, state why explicitly and use the available incident evidence to guide measurements. Revisit the comparison when later evidence changes your understanding of the failure.

**Artifact**: Reproduction steps/command, measurements, and comparison with incident evidence, including differences or unavailable evidence. If reproduction isn't achievable, an explicit statement of why and what alternative strategy you're using instead.

### Checkpoint 4: State your ground

Without a written record of what you're standing on, a hypothesis that contradicts a system guarantee goes unnoticed — the debugger investigates a condition the system has already ruled out.

Before forming hypotheses, write down what you're treating as true and where each belief comes from. Separate guarantees and contracts from raw observations and their interpretations. Keep the artifact sources and version/configuration context from checkpoint 2. Measurements establish what happened in the measured runs; an interpretation of those measurements is a separate claim.

Sources of these beliefs, roughly ordered by how costly they are to question:

- **Language and runtime guarantees.** Properties the language or runtime enforces. For operations governed by Pony's type system, reference capabilities guarantee no data races and the type system guarantees a `val` reference is never written to. Disputing these guarantees within that scope means asserting a compiler or runtime bug. Checking their applicability does not: incorrect FFI use or foreign code can violate them without such a bug.
- **Protocol and design contracts.** Properties the system's design is supposed to enforce. Phase 1 of a protocol clears all external references before phase 2 begins. A constructor establishes an invariant that methods depend on. Questioning these means asserting the implementation doesn't match the design.
- **External specifications.** Properties documented in an external authority — an RFC, a C library's API contract, a hardware manual. Relevant when debugging FFI bindings, protocol implementations, or codec conformance. Questioning these means asserting the specification is wrong, version-mismatched, or misread.
- **Empirical observations from this session.** Things you've verified by running code — a specific value at a specific point, a code path that executes, a timing you measured. These are evidence, but they're samples; they don't prove the general case.
- **Code-reading inferences.** Things you concluded by reading the source. These are the most fragile — you may have missed a branch, misread control flow, or not noticed an override.

State each belief, its source, its scope, and what it rules out. Check whether a measurement's collection method and context support the interpretation. Preserve the raw evidence when an interpretation changes. Uncertainty about a measurement does not justify discarding a language guarantee. This list is the ground for checkpoint 5's investigation loop — the reference point for checking whether a hypothesis contradicts a guarantee or an established observation.

**Artifact**: Guarantees, contracts, observations, and interpretations, each with its source, scope, and what it rules out; unresolved assumptions stated explicitly.

### Checkpoint 5: Investigation loop

This is the core of debugging. It's an OODA loop — observe, orient, decide, act — not a linear sequence. You rarely understand the full picture at the start. The goal is to narrow the problem space iteratively until you can explain all symptoms.

**Each iteration:**

1. **Orient**: State a hypothesis about some subset of the problem. It doesn't need to explain everything yet — but be explicit about what it covers and what remains unexplained. "I think [cause] because [evidence]. This would explain [symptoms A and B] but not [symptom C]." Name which beliefs from checkpoint 4 the hypothesis depends on, and whether it contradicts any. Leaving a symptom unexplained is allowed; contradicting an established relevant observation is not.

2. **Decide**: Design an experiment that would support or refute this hypothesis. What would you expect to see if it's right? What would you expect under competing explanations? If the available observations do not distinguish the candidates, seek a measurement from another layer or view of the execution. If that measurement is unavailable, name it and state which explanations remain indistinguishable. You may compare candidates against observations as supported, contradicted, or unknown; unknown is not support, and the candidates need not cover every possible cause.

3. **Act**: Run the experiment — instrument the code, add logging or assertions, run the reproduction. Report what was observed.

4. **Observe**: What did the evidence show? This is where you branch. If the prediction held, *refine* — narrow the hypothesis toward a more specific cause. If an established observation contradicts the prediction, *replace* — form a new hypothesis from what the evidence actually showed. If an apparent contradiction depends on an unverified measurement assumption, investigate that assumption before deciding whether to refine or replace. State the assumption and the measurement needed to verify it; the candidate remains unresolved during that investigation. If the result was unexpected, update your model of the problem space before choosing the next step.

Then loop. Each iteration should narrow the space — ruling out possibilities, supporting parts of the causal chain, surfacing new information. Keep going until your hypothesis accounts for all established relevant observations.

**Artifact — debugging logbook**: Maintain a single cumulative document across iterations, retaining checkpoint 4's sources and distinctions between observations and interpretations. Each entry records the hypothesis, the prediction, the experiment, the outcome with its source and context, and the decision — refine, replace, or investigate a measurement assumption. Record the resulting hypothesis or the assumption and measurement to investigate next. Record unresolved assumptions and changes to interpretations without rewriting raw evidence. Read it top to bottom: you narrow the hypothesis with each supported prediction, change direction when an established observation contradicts it, or verify a measurement assumption before deciding. Without accumulation, per-iteration notes are disconnected snapshots.

**When the symptom is nondeterministic**: Use the observed differences to choose alternatives to investigate. Scheduling, input variation, resource limits, environment differences, and code logic are possible causes; intermittency alone does not establish any of them. Compare failing and successful runs, then measure what would distinguish the plausible explanations. Code paths that look equivalent may still execute with different state or timing.

**When evidence supports a hypothesis**: Supporting a broad hypothesis does not end investigation — narrow further. Ask what more specific cause, within the region you just measured, would produce exactly these symptoms. "The parser drops trailing fields" becomes "the parser treats repeated delimiters as a single delimiter, consuming the empty field between them." Each refinement is a new hypothesis with its own prediction and experiment. A prediction holding does not prove that only this explanation is possible. Stop refining when the hypothesis names a specific mechanism whose execution you have measured and whose causal links you can support.

**When evidence refutes a hypothesis**: Reject the candidate, or identify and verify the assumption on which the apparent contradiction depends. Do not reinterpret the raw observation to preserve the candidate. Once refuted, form a NEW hypothesis from what the evidence actually shows. Do not shift the old hypothesis — "maybe it happens earlier" is the same hypothesis moved upstream. That's defending a theory, not following evidence.

**When a hypothesis contradicts an invariant**: A hypothesis that requires a guarantee or contract from checkpoint 4 to be false is not investigated at face value. Exhaust hypotheses consistent with the invariant first. When nothing else explains the symptoms, question the invariant — but treat that as a separate, explicit investigation with its own evidence requirements. You need direct evidence that the invariant doesn't hold, not just an inability to explain the symptoms another way. If the invariant falls, go back to checkpoint 4 and revise the list — every conclusion built on that invariant is now suspect.

**If stuck after 2-3 iterations without progress**: You are likely anchored to a bad hypothesis. Spawn a fresh-eyes subagent with the original problem, what you've tried, your current hypothesis, and the evidence sources. Have it verify assumptions, generate alternatives, and try to falsify the control comparisons, reproduction fidelity, and unsupported causal claims. Act on its findings — don't dismiss them to defend your original theory. Agreement between agents is not evidence that a code path executed.

**Exit condition**: You can explain all established relevant observations, including the distinguishing incident measurements and applicable controls, and have evidence supporting each link in the causal chain. Cite that evidence and state limits where incident evidence or reproduction is unavailable. Those limits do not prevent proceeding when other evidence supports each causal link. You need not prove a unique cause or investigate every conceivable explanation. If plausible alternatives leave the incident's cause unresolved, stay in investigation and seek a measurement that distinguishes them. If that measurement is unavailable, report a blocked diagnosis and the measurement needed; recording the uncertainty does not satisfy this exit condition. Proceed to checkpoint 6 only when the causal explanation is supported.

### Checkpoint 6: Find where the cause reaches

You know why the bug happens. Before you decide what to change, find where else that cause reaches. You cannot pick where to fix until you know what the fix has to cover.

Bound the search by the mechanism checkpoint 5 gave you — the function, the field, the invariant that fails. That is what tells you when you are done, and it is why this is a directed search rather than a walk through the codebase.

Start where the bug was reported, and follow the cause outward. Often it simply reaches further than one place: the same bad value arriving at three call sites when only one of them got reported.

Sometimes it is worse than that. Two pieces of code are supposed to behave the same way, and nothing makes them. The difference between them is the defect, and the bugs it produces need not resemble each other at all — a crash in one, a hang in the other, a feature quietly absent from a third. What matters is that one thing produced them all. That divergence will keep producing bugs until you remove it.

When that is what you have, the second bug is not a second issue to file. It is one defect showing up twice — so long as the two really are supposed to behave the same. When they are not, you have two defects, and the test below tells you which case you are in.

Go and look. You cannot find those places from what you already know.

**Three signs a divergence has been papered over instead of removed.**

The first is in the fix you were about to write. It adds a field or a flag to one copy of something so that copy matches the other. Making two things agree by hand admits that nothing makes them agree.

The second is already in the code: a comment saying two things must change together. Take it seriously. A comment pairing two things that sit near each other — same type, same file, a few lines apart — is not documenting a coupling; `pony-comments` is explicit that a pairing with both ends in one file is not one. So go and look at what it is holding together. Often it is a defect somebody wrote down instead of removing: a value stored in a field where it should have been passed, two branches that should have been one. Writing it down is what stopped it looking like a bug. Sometimes it is a real invariant the code cannot express, and then it stays. You will not know which until you look. If what you find is the cause of the bug you came for, removing it is the fix, and checkpoint 7 is where you decide the place. If it is a tidy-up you happened to notice, restructuring it is a decision to raise, not one to fold into a bug fix.

The third is in the documentation. When one of two paths that should act alike is missing something, and the gap got written into the docs, the absence has been recorded as if it were a design choice.

**When it really is two defects.** The test is not whether the two places share code. It is whether they are supposed to behave the same. Two read loops that must respond identically to the same events are one defect, however little code they share. A missing check in a parser and a missing check in an unrelated request handler are two, however alike they look — fix the one you came for and record the other as a suspected issue (`pony-vet-suspected-issues`). Two defects is the answer that costs you less work right now, so be careful reaching for it. You have to be able to say why the two are *not* supposed to behave the same. If you can't, treat them as one defect.

Note what you saw anyway. The same mistake made independently twice is the best evidence you will get that the code permits a mistake it should make impossible. That is a design finding, worth more than either bug on its own. Raise it; don't quietly fix it.

That advice is for two defects. One defect in two places doesn't get raised and left alone — checkpoint 7 decides where it gets fixed.

**Artifact**: What you searched — the places the bad value can reach, and the code that ought to behave like the code the bug was reported in. How you found them, and what the cause does at each. Every place it reaches, the reported one among them. "Only the reported site" is a real answer, and it still has to name the places you ruled out.

### Checkpoint 7: Find where the fix belongs

Now pick the place to change. It has to cover every place checkpoint 6 found.

Name it. Ask whether any of those bugs could still happen by a route that change does not cover. If one could, that was the wrong place — either something upstream is still producing the bad value and your fix catches it late, or the same bad value reaches call sites your change does not touch. Move and ask again.

Sometimes no existing place covers everything. Two pieces of code that must agree, with nothing making them agree, have no shared place to fix, and that absence is the defect. Making them agree by hand, in each of them, is not the fix. Build the thing that makes them agree, and fix it there.

That is a larger change than the report asked for. Say so — in the plan, in the pull request, wherever the people who have to live with it will read it. Building it quietly is how a bug fix becomes a rewrite nobody agreed to.

If the cause reaches places you are not going to fix, that is a decision to raise, not a line to write here. If it cannot be fixed cleanly at any place you are able to change, say so and stop. Don't write the special case.

**Artifact**: The place you will change, and why nothing checkpoint 6 found still breaks once you have changed it. If you stopped instead, that is the artifact: the places you considered, why none of them can hold a clean fix, and what would have to change for one to exist.

### Checkpoint 8: Fix and verify

Fix the cause, in the place checkpoint 7 identified. Explain why this addresses the cause, citing the causal evidence from the logbook. A sleep, a retry, or a "just check again" that masks the problem is not a fix. Run the reproduction and recheck the distinguishing incident measurements and applicable controls. Confirm the expected change in the mechanism as well as the symptom. If incident evidence or reproduction is unavailable, state what you checked and what remains unverified. For the other places checkpoint 6 found, build a check for each — and where you can't build one, say so rather than assume.

Read the fix you just wrote. Can you say why that code is there without mentioning the bug report? "The reader never returns an empty list" needs no report to make sense. "We check for an empty list here, because empty configs crashed" cannot be explained without one — the code is shaped like the report instead of like the program. If you need the report to explain the fix, you fixed the report. Go back to checkpoint 7.

**Artifact**: The fix, the rationale with causal evidence references, verification measurements and control comparisons, and explicit limits on what was verified.

## Honest use

The artifacts should reflect actual investigation, not be written retroactively after you've already decided on a cause. If you find yourself writing the characterization after you've already started coding a fix, you skipped the protocol — back up.

Checkpoint 6 is where this matters most. "I looked and found nothing" and "I did not look" produce the same sentence. Only one of them is true, and only you know which.
