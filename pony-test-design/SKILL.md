---
name: pony-test-design
description: Two-stage ensemble for planning meaningful tests. Load when writing tests for new features or reviewing test quality. Counters the tendency to write tests that exercise the stdlib instead of your code. Has full (8-persona) and lightweight (5-persona) modes.
disable-model-invocation: false
---

# Test Design

Load this skill when writing tests — for new features, bug fixes, or
standalone test work. The core problem it addresses: tests that look right but
aren't. They pass, they get merged, but they're testing the stdlib, or they
can't actually fail when the code breaks, or they miss the adversarial cases
entirely.

A single agent applying the pony-test-design disciplines will still pattern-match —
the disciplines become post-hoc rationalizations for tests it was already going
to write rather than actual constraints on the planning. The two-stage ensemble
forces genuine exploration of what needs testing and genuine scrutiny of
whether the proposed tests accomplish it.

## Mode selection

The skill has two modes: **full** and **lightweight**. The orchestrator
selects the appropriate mode based on the criteria below and proceeds.
Report the mode choice when presenting results — the human can request
full mode if lightweight was used and they want deeper coverage.

**Full mode** is the default. Use it when:

- Testing a new feature or subsystem with substantial test work
- The right test approach is genuinely uncertain
- Code under test has complex state, many code paths, or crosses multiple
  boundaries
- Multiple test strategies need to be explored and compared

**Lightweight mode** is for bounded test work within established patterns:

- Adding a single regression test for a known bug
- Extending an existing test pattern to a new variant
- Testing a simple function with clear inputs/outputs
- Adding tests that follow an established pattern in the codebase
- The task can be described as "add a test for X" where X is well-understood

When in doubt, use full mode. Lightweight is appropriate when the test
work is clearly bounded — the orchestrator should be able to state what
makes it bounded and why fewer evaluation personas are sufficient.

## Process: full mode

Test planning runs in two stages with a feedback loop. Load `pony-ensemble` for
the mechanical process; the personas defined in this skill replace the generic
attention focuses.

### Relationship to Ensemble Workflow

This skill uses the ensemble workflow with domain-specific customizations.
Stage 1 (planning) runs as a standard ensemble with 3 personas. Stage 2
(evaluation) runs as a second ensemble with 5 personas, using the Stage 1
synthesis output as its input. The two-stage loop and finding categorization
(Rejection/Adjustment/Tension) are additions specific to this skill — the
base ensemble protocol handles agent spawning, triage, and synthesis
mechanics.

### Stage 1: Planning

Three planning personas explore the code under test from different directions
in parallel. Each applies all the disciplines below but enters the problem
from a different starting point. The decorrelation comes from where they
start, not what they know. Persona definitions are in `personas/planning/`.

On first invocation, the orchestrator provides each planning persona with:
the task description (what code to test and why), paths to the code under
test, and paths to any existing tests. On subsequent iterations (after
evaluation feedback), personas also receive the prior candidate test strategy
and the categorized findings — see "The loop" below.

| File | Focus |
|------|-------|
| `boundary-focused.md` | Starts from implementation — maps decision points, branches, state transitions |
| `failure-focused.md` | Starts from "how does this break?" — works backward from bad outcomes |
| `contract-focused.md` | Starts from public API without reading implementation first |

### Planning persona output format

Each planning persona produces a candidate test strategy as a structured list.
Each proposed test includes:

- **Test name**: Descriptive name for the test
- **Coverage target**: What code path, boundary, contract, or failure mode
  this test exercises
- **Input approach**: Property-based or example-based, with rationale
- **Expected assertions**: What specifically is checked, and on what dimension
- **Rationale**: Why this test matters — what bug would it catch?

The standard ensemble agent output format (Key decisions, Uncertainties,
Assumptions) applies alongside this structured list.

Stage 1 synthesis produces a candidate test strategy using the standard
ensemble synthesis process. The Integrated Result must maintain the structured
list format — each proposed test retains its fields so evaluation personas
can assess them systematically. The synthesis should pay special attention to:

- Where the boundary-focused persona's implementation-derived tests overlap
  with the contract-focused persona's API-derived tests — convergence from
  inside-out and outside-in is strong signal that those tests matter
- Where the failure-focused persona identified scenarios the others missed —
  these are the highest-value additions
- Whether the three personas chose different input approaches (property vs.
  example) for the same behavior — the disagreement usually reveals whether
  an invariant exists
- Whether the personas are testing at different scope levels (public API vs.
  internal helpers vs. dependency interactions) — resolve scope disagreements
  explicitly rather than merging tests from incompatible levels
- Where the contract-focused persona proposes a test for a documented promise
  that the boundary-focused persona finds no implementation boundary for —
  this may indicate an untested code path or a test that would exercise the
  stdlib rather than the code under test

### Stage 2: Evaluation

Five evaluation personas stress-test the candidate test strategy in parallel.
Their input is the Integrated Result from Stage 1 synthesis — the candidate
test strategy with its proposed tests, input approaches, and expected
assertions. They evaluate the test strategy against the code under test —
their findings are about the strategy's quality, not bugs in the code. Persona
definitions are in `personas/evaluation/`.

| File | Focus |
|------|-------|
| `specificity.md` | Are these tests testing your code or the stdlib/framework? |
| `coverage.md` | Systematic gap analysis — missing edge cases, boundaries, adversarial scenarios |
| `counterfactual.md` | Can each proposed test actually fail when the code breaks? |
| `property-opportunity.md` | Would properties provide stronger coverage than examples? |
| `wildcard.md` | What all 7 other personas missed |

For the wildcard persona specifically: include the identity statement (first
paragraph) from each of the other 7 personas so the wildcard knows what
territory is already covered.

Before spawning evaluation personas, create a temporary directory for evidence
files (`~/tmp/test-eval-<timestamp>/`). Each persona writes its detailed
analysis to a file in this directory and returns a structured summary to the
orchestrator. The synthesizer works from summaries and digs into evidence
files only when it needs to examine a finding more closely. This prevents
context overload during synthesis.

Evaluation personas identify problems and assess impact — they do not
categorize their own findings as Rejection/Adjustment/Tension. Categorization
is the synthesis step's responsibility.

### Evaluation persona output format

Each evaluation persona produces two artifacts:

**Evidence file** — written to the path provided by the orchestrator. Contains
the full detailed analysis: every finding with complete evidence, full test
strategy excerpts, detailed reasoning, and complete pass/fail evaluations.
This is the authoritative record.

**Summary** (returned to orchestrator) — a structured summary for the
synthesizer to work from:

**Findings** — ordered by impact (Structural > Significant > Minor). Each:

- **Test element**: What is being evaluated — reference proposed tests by
  their test name, then cite the specific field (input approach, assertion,
  coverage target) under scrutiny
- **Concern**: What the problem is
- **Impact**: Structural (requires rethinking the test approach), significant
  (requires notable changes to the candidate), or minor (a local
  change; the rest of the candidate is unaffected)
- **Evidence**: Brief — full evidence is in the file
- **Suggested change**: Write it whenever you can. A concern you can name but
  cannot resolve is still a finding — say so, and say what blocks you.

Impact is what the finding costs the candidate: how much of it has to
change. It is not permission to leave the finding alone — report a minor
finding exactly as you report a structural one, and stage 2 synthesis categorizes
every finding, at every impact level.

The impact assessment helps the synthesizer with categorization without
pre-empting it. A persona's "structural" assessment is a strong signal toward
Rejection, but the synthesizer may disagree if it sees the concern addressed
by another persona's suggestion.

**Passes** — things checked that look correct. Brief.

**Uncertainties** — things the persona couldn't determine, and why.

Stage 2 synthesis works from the persona summaries and categorizes each
finding. Provide the paths to each persona's evidence file so the synthesizer
can dig in when it needs more context — when impact assessments conflict, when
a finding's summary is ambiguous, or when it needs to verify the evidence
supports the concern.

Instruct the synthesizer that evaluation findings are independent concerns
from different analytical lenses, not alternative approaches to the same
problem. The dominance heuristic from `pony-synthesize` ("when one agent's output
is clearly superior, use it") does not apply — a specificity finding and a
coverage finding aren't competing, they're additive. Collect all findings for
categorization.

Stage 2 synthesis categorizes each finding:

- **Rejection**: A structural problem that invalidates the test approach.
  The candidate cannot be fixed by adjustment — the planning personas need to
  rethink. The rejection includes why the approach fails and what constraint
  it violates. Example: the entire test strategy exercises stdlib behavior,
  not the code under test.
- **Adjustment**: A specific aspect that needs to change, but the overall
  approach is sound. Becomes a constraint for the next planning iteration.
  Example: a specific test should use a property instead of an example, or a
  boundary condition is missing.
- **Tension**: A fundamental conflict that the personas cannot resolve — it
  requires human judgment. Example: testing a behavior properly requires
  reaching into internals, but the design doesn't expose observation points.

### The loop

After stage 2 synthesis:

1. If there are no rejections or adjustments (only tensions, if any), the
   loop terminates. Present the test strategy with any tensions for human
   review.
2. If there are adjustments and/or rejections, feed them back to the planning
   personas. Each planning persona receives: the prior candidate test
   strategy, the code under test, and the categorized findings. Rejections
   include the rationale for why the approach failed — planning personas
   should explore a different test strategy, not patch the rejected one.
   Adjustments include the specific change needed and why — planning personas
   should revise the candidate to incorporate them as constraints.
3. The planning personas run again with this context, producing a revised
   candidate.
4. Evaluation runs again on the revised candidate. Evaluation personas run
   with fresh context (no knowledge of prior evaluations). The synthesis step
   receives the full history so it can track convergence.
5. Repeat until clean or until convergence failure is detected.

### Convergence failure

The orchestrator monitors the loop for signs that it isn't converging:

- The same evaluation concern keeps appearing across iterations, even after
  planning revisions attempt to address it
- Rejections and adjustments are contradicting each other (fixing one
  evaluation concern breaks another)
- The test strategy is growing more complex with each iteration rather than
  settling

Because evaluation personas run with fresh context, they may re-raise
concerns that were addressed in a prior iteration — but in a narrower form.
The synthesis step (which has the full history) must distinguish progress
from non-convergence: if a concern from round N reappears in round N+1 at a
narrower scope (fewer tests affected, smaller part of the strategy), that's
progress. If it reappears at the same or broader scope, that's a
non-convergence signal.

When a convergence failure is detected, the orchestrator stops the loop and
escalates to the human: "Here's the fundamental tension — these concerns pull
in opposite directions, and we need you to decide which matters more." This is
not a failure of the process. Surfacing genuine tensions is one of its primary
outputs.

### Output

The final output includes:

- **Accepted test strategy** (if one emerged): The candidate that passed
  evaluation, with proposed tests, input approaches, and expected assertions.
- **Rejected strategies**: Each candidate that was rejected during the loop,
  with the rejection rationale. These document explored territory and why it
  didn't work.
- **Unresolved tensions**: Findings categorized as tensions that require human
  judgment.

If the loop terminated via convergence failure rather than a clean evaluation,
there is no accepted test strategy — only the history of attempts, the
rejections, and the tensions.

## Process: lightweight mode

Lightweight mode uses fewer personas and a single pass. It keeps all three
planning personas but reduces evaluation to two personas and drops the
feedback loop. Load `pony-ensemble` for the mechanical process.

### Stage 1: Planning

Three planning personas explore the code under test from different directions
in parallel — the same as full mode. The same disciplines apply; the
decorrelation still comes from different entry points.

| File | Focus |
|------|-------|
| `boundary-focused.md` | Starts from implementation — maps decision points, branches, state transitions |
| `failure-focused.md` | Starts from "how does this break?" — works backward from bad outcomes |
| `contract-focused.md` | Starts from public API without reading implementation first |

Stage 1 synthesis produces a candidate test strategy using the standard
ensemble synthesis process. The same synthesis guidance as full mode applies:
inside-out/outside-in convergence is strong signal, failure-focused scenarios
the others missed are the highest-value additions, and disagreements on input
approach (property vs. example) reveal whether an invariant exists.

### Stage 2: Evaluation

Two evaluation personas stress-test the candidate. The specificity evaluator
always runs. The second slot is context-dependent — if the human specifies
which evaluator to use, use that. Otherwise the orchestrator picks whichever
lens is most relevant to the task:

| When | Pick |
|------|------|
| Tests have non-obvious assertions or complex code paths | `counterfactual.md` |
| Code under test has many branches, states, or variants | `coverage.md` |
| Tests use example-based inputs for behavior with potential invariants | `property-opportunity.md` |

Pick whichever is closest — every test strategy has some risk profile. If
multiple conditions apply, pick the most relevant one. If the reason for
picking a particular evaluator is a code characteristic that also appears
in the full-mode selection criteria, that's a signal the task warrants full
mode — don't use the persona pick to compensate for a wrong mode
selection.

Before spawning evaluation personas, create a temporary directory for
evidence files (`~/tmp/test-eval-<timestamp>/`), same as full mode.
Each persona writes its detailed analysis to a file in this directory and
returns a structured summary. Evaluation personas use the same output
format as full mode (evidence file + summary with findings ordered by
impact, passes, uncertainties).

Stage 2 synthesis categorizes each finding as Rejection, Adjustment, or
Tension using the same scheme as full mode. If the 2 personas collectively
produce more findings than expected for the test scope, note this explicitly
— a high density of findings on a small test task suggests the code under
test is more complex than it appeared and may warrant full mode.

### Not included in lightweight

- **Wildcard** — the wildcard's value scales with change complexity and the
  number of other personas whose territory it needs to look beyond. With only
  2 focused evaluation personas on a small test task, there's insufficient
  covered territory for the wildcard to add meaningful signal.

### No loop — single pass

Lightweight mode does not iterate. After Stage 2 synthesis:

- **Adjustments and tensions**: Present the test strategy with findings to the
  human. Adjustments are expected to be small enough that the orchestrator or
  human can apply them directly. If adjustments collectively amount to
  replanning the test strategy rather than tweaking it, that's the same
  escalation signal as high finding density — present it to the human.
- **Rejection**: The test approach is wrong. Present the rejected candidate,
  the rejection rationale, and all other findings to the human. The human
  decides what to do — escalate to full mode, fix it directly, rethink the
  problem statement, or something else. Lightweight doesn't prescribe the
  response; it presents the information.

If the review produces an unexpectedly high density of findings relative to
the test scope, if a finding reveals the test approach is fundamentally wrong,
or if findings reveal the code under test is more complex than the mode
selection assumed, the orchestrator presents this to the human. The human
decides what to do — the same options apply.

### Output

The final output includes:

- **Candidate test strategy**: With proposed tests, input approaches, and
  expected assertions.
- **Adjustments**: Specific changes needed, small enough to apply directly.
- **Tensions**: Conflicts requiring human judgment.
- **Rejection rationale**: If applicable — the structural finding and why the
  test approach was rejected.

## The disciplines

These are the foundation each persona builds on. Every agent applies all of
them.

### 1. Test the Code You Wrote

Before writing a test, ask: "Does this exercise code I wrote, or code the stdlib already tests?" If your feature is a thin wrapper around a stdlib function, testing the wrapper in isolation tests the stdlib. Test through the integration boundary instead — the path where your code parses input, makes decisions, calls the stdlib function, and produces output.

**Bad**: Your feature calls `sort(array)` internally. Your test creates an array, calls `sort` directly, and asserts it's sorted. That tests the sort function, not your feature.

**Good**: Your feature parses a CLI flag, collects items, sorts them, and prints the result. Your test creates the system with controlled CLI args and a captured output stream, then verifies the printed output is sorted. This exercises your argument parsing, collection logic, and output formatting — the code you actually wrote.

### 2. Test at Integration Boundaries

Find the narrowest boundary that still exercises your actual code paths. For an actor, this means creating it with controlled inputs and observing its outputs — not testing extracted helper functions in isolation.

Before concluding something is untestable, check what's actually available: public constructors, injectable dependencies, interface types you can implement. The answer is often "constructable with controlled inputs" rather than "impossible to test."

### 3. Each Test Owns Its Inputs

Shared test fixtures create hidden coupling. Changing the fixture breaks every test that uses it, even if those tests don't care about the change.

Each test should define its own inputs inline. This makes tests independent — you can change one test's inputs without touching the others. The slight repetition is worth the decoupling.

### 4. Properties and Edge Cases

Favor property-based tests over example-based unit tests. An example-based test says "this specific input produces this exact output." A property test says "across many inputs, this invariant holds." Examples test one point; properties test the rule. When a PBT framework isn't available, write the property loop manually — iterate over inputs, collect results, assert the invariant. Load `pony-pbt-patterns` for generator design and coverage patterns when writing PBT.

Use example-based tests for edge cases and boundary conditions. Edges are where bugs live: zero, empty, one element, maximum value, off-by-one at a threshold, the exact boundary between valid and invalid. These deserve explicit tests with known inputs and exact expected outputs because you're testing a specific decision point, not general behavior. Properties and edge-case examples complement each other — properties cover the space, examples nail the borders.

### 5. Magic Values Are Unverified Assumptions

If a test uses a specific input and assumes it triggers a particular behavior (e.g., "this value is large enough to overflow," "this string contains invalid characters"), that's an unverified assumption. Either:
- Compute the expected output empirically and assert exactly (makes the assumption explicit and verifiable)
- Test the property across multiple inputs so no single value matters

Never rely on "this input probably triggers the behavior" — verify it or test the property.

### 6. Counterfactual Testing

After writing new tests, temporarily break each assertion to confirm it fires. A counterfactual that passes (assertion doesn't fire) means the assertion is weak — treat this as a bug found, not just a confidence check. Always assert on the *specific dimension* being tested, not the whole output. For property tests, also verify the generator covers the relevant range before concluding the assertion is weak.

**Workflow**: After a new test passes, do NOT report success yet — do counterfactual checks first. Run only the specific test during iterations, not the full suite. Full suite once at the end.

### 7. Consistent Rigor Across Variants

When code implements the same pattern across multiple variants (type families, format handlers, similar APIs), test quality tends to taper — the first variant gets careful attention, later ones get less. If the first variant has boundary tests at every transition point, every other variant should too. When reviewing, compare thoroughness across variants; inconsistency is a smell.

### 8. Tests Are Part of Done

Test coverage gaps for new code are not follow-up work. Tests for code introduced in the current change are part of "done" — don't defer them. Only tests for pre-existing untested code belong in follow-up issues. Plans for test work must include the specific command(s) to build and run the tests.

## Anti-patterns

These are the specific failure modes this skill exists to prevent. If you catch
yourself doing any of these, stop and reorient.

**Testing the stdlib instead of your code.** If your test would still pass with
your feature code deleted, it's not testing your feature. This is the single
most common failure mode — the test exercises a library function, not the code
that calls it.

**Planning tests without reading the code under test.** If the test strategy
doesn't reference specific decision points, branches, or state transitions in
the actual code, it was planned from assumptions about what the code does, not
from what it actually does. At least one planning persona (boundary-focused)
must read the implementation.

**All examples, no properties.** If every proposed test uses a specific input
and checks a specific output, ask whether any of the tested behaviors have
underlying invariants. Properties are stronger than examples for invariant
behavior — they test the rule, not one point on it.

**Magic values without justification.** A test that uses `input = 255` without
explaining why 255 is significant is making an unverified assumption. Either
the value is a boundary (document which boundary) or it doesn't matter (use a
property).

**Consistent first test, sloppy rest.** When testing multiple variants of the
same pattern, the first variant gets careful boundary tests and the rest get
smoke tests. If the pattern has N variants, all N need the same rigor.

**Skipping evaluation.** When running the pony-test-design ensemble, planning tests
and going straight to implementation without running the evaluation stage. The
evaluation personas catch structural problems — stdlib testing, weak
assertions, missing properties, coverage gaps — that the planning personas
aren't looking for.

**Proposing tests that can't fail.** A test that asserts on the entire output
or checks a tautological property ("the result is not nil" when the function
never returns nil) provides false confidence. Every proposed test should have a
concrete code mutation that would make it fail.

**Mirroring internal layout instead of asserting on the contract.** A test that
copies constants, offset arithmetic, or internal geometry from the code under
test is testing that the implementation matches a snapshot of itself — not that
it upholds a promise. Assert on observables the design guarantees. When the
geometry changes, contract-level assertions still hold; mirrored-constant
assertions break on every refactor.
