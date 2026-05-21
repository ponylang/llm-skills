---
name: pony-code-review
description: Ensemble code review with specialized reviewer personas. Has full (8-persona) and lightweight (3-persona) modes. Load when conducting a code review of a PR, branch, or local changes.
disable-model-invocation: false
---

# Code Review

Ensemble code review that synthesizes findings from specialized reviewer personas. Has two modes: full (8 personas, iterative re-review) and lightweight (3 personas, single pass). Not for one-line config changes or typo fixes — ask permission to skip review for those.

## Mode Selection

The skill has two modes: **full** and **lightweight**. The orchestrator selects the appropriate mode based on the criteria below and proceeds. Report the mode choice when presenting results — the human can request full mode if lightweight was used and they want deeper coverage.

**Full mode** is the default. Use it when:

- The change has non-obvious scope — a feature, a refactor that moves boundaries, a bug fix with wide blast radius
- The change touches multiple subsystems or crosses ownership boundaries
- "Is the approach right?" is genuinely uncertain
- The change is large enough that a single review pass might miss interactions between parts

**Lightweight mode** is for small, bounded changes within established patterns:

- Bug fix in a well-understood area
- Simple refactor (rename, extract, inline)
- Straightforward test addition
- Small feature following existing patterns
- Change touches a single subsystem with clear boundaries

When in doubt, use full mode. Lightweight is appropriate when the change is clearly bounded — the orchestrator should be able to state what makes it bounded and why fewer personas are sufficient.

Note: the pony-software-design skill's lightweight mode follows a similar pattern (mode selection, single pass, escalation) but reduces differently — it has two stages and shrinks only the evaluation stage (5→2 personas). Code-review has a single stage, so the reduction is in persona count (8→3). The shared pattern is the mode selection and escalation structure.

## Invocation Modes

These modes apply to both full and lightweight:

**Integrated (pre-PR pipeline):** The implementer runs pony-code-review as part of their pre-PR workflow. In full mode, findings are triaged, unambiguous ones are fixed, and the loop repeats until clean. In lightweight mode, findings are triaged and fixed in a single pass. See the relevant process section below.

**Standalone:** Invoked directly on an existing PR, branch, or local changes for a one-shot review. The process section for the selected mode applies as-is.

## Relationship to Ensemble Workflow

Use the ensemble workflow with review-specific customizations. Load `/pony-ensemble` for the mechanical process. This skill replaces the generic attention focuses with review personas (8 for full mode, 3 for lightweight) and replaces the generic agent output format with the review-specific format defined below.

The Adversarial persona satisfies the ensemble's "fix reviews require an adversarial focus" requirement — when the review target is a fix, the Adversarial persona naturally focuses on showing the fix is incomplete per its identity statement.

Persona agents write detailed evidence to files and return structured summaries to the orchestrator. The synthesizer works from summaries and digs into evidence files only when it needs to examine a finding more closely. This prevents context overload during synthesis.

The pony-synthesize skill's output format (Integrated Result, Synthesis Rationale, etc.) is not a natural fit for code review. The orchestrator instructs the synthesizer to produce output in the review-specific final format (below) rather than the generic synthesizer format. No changes to `/pony-synthesize` itself.

## Design Values

When principles conflict, these values set the priority. We value the left side over the right — but the right side still matters when the left isn't at stake.

**API safety over API minimality** — an error-prone API should be fixed even if the fix adds surface. Prefer solutions that don't expand the API, but never leave a footgun to preserve minimality.

**Correctness over performance** — never sacrifice correctness for speed. Get it right first, then optimize. A faster wrong answer is still wrong.

**Correctness over concision** — correct but verbose beats concise but wrong. Don't simplify code or APIs at the cost of correct behavior.

**Security over performance** — never skip validation at trust boundaries for speed. Optimize how you validate, not whether you validate. Security is correctness.

**Interface simplicity over implementation simplicity** — accept a harder implementation to give users a clean interface. The consumer's experience matters more than the implementer's convenience.

**Performance over interface simplicity** — runtime speed matters more than programmer convenience. It's acceptable to make things harder on the user to improve performance, but never at the cost of correctness.

**Simplicity over consistency** — don't force artificial consistency when it makes things harder to use. If two similar things genuinely need different interfaces, let them be different.

**Explicitness over implicitness** — when the language allows something to work by magic (implicit conversions, convention-based wiring, unnamed dependencies), prefer the version that states what's happening. The cost of a few extra characters is less than the cost of reconstructing hidden knowledge.

**Type safety over convenience** — use the type system to encode constraints even when it's more work. Distinct types for distinct semantics, validated wrappers over raw primitives, explicit error vocabularies over generic errors. "We could just use a String here" is almost always wrong.

**Changeability over predictive design** — make designs modular and replaceable so future needs can be accommodated, but don't add abstractions, extension points, or features for changes that haven't happened yet. Easy to modify beats designed for a specific predicted modification.

## Process: Full Mode

1. **Identify the review target.** PR URL, branch name, or local changes. If not specified, ask. Resolve the target into concrete instructions for agents: the base branch to diff against, the git diff command or `gh pr diff` command to run, and any design doc or issue URLs for context.

2. **Build and run tests once.** Capture the build output and test results. These results are provided to persona agents that need them — no agent runs tests itself. If the build fails or tests fail, proceed with the review anyway — provide the failure output to all personas and note whether the failure is pre-existing or introduced by the change.

3. **Create a temporary directory for evidence files.** Use `~/tmp/code-review-<timestamp>/`. Each persona will write its detailed evidence to a file in this directory. Generate the file path for each persona (e.g., `correctness-evidence.md`) and pass it in the prompt.

4. **Spawn 8 persona agents in parallel** as Tasks with subagent_type="general-purpose" and model="opus". Each agent's prompt includes:

   - The persona document, read from the corresponding file in `personas/`. When a persona's context loading references an external skill (e.g., `/pony-test-design`, `/pony-pbt-patterns`, `/pony-ref`), read that skill's content and include it in the agent prompt.
   - The code-review principles: read `references/principles.md` (alongside this skill) and include its content in the agent prompt, the same way referenced skills are injected above. Also instruct the agent to read the project `CLAUDE.md` if one exists (not all projects have one; if absent, note it and proceed) and to follow its conventions, including loading any skills it references.
   - The review target: base branch, diff command, PR URL, and any related issue/discussion URLs.
   - Instructions to read all changed files in full (not just diffs), plus supporting files needed for context.
   - For Correctness, Adversarial, and Tests personas: the captured build output and test results from step 2.
   - The shared persona output format (below), including the evidence file path and instructions to write detailed evidence to that file and return a summary.
   - Instructions to run a reviewer loop before returning — the reviewer checks the persona's analysis for coherence, completeness, and evidence quality, not the underlying code a second time.
   - Instructions that this is an ensemble agent — return findings to the orchestrator, don't take external actions.

   **For the Wildcard persona specifically:** include the identity statement (first paragraph) from each of the other 7 personas so the wildcard knows what territory is already covered.

5. **Triage agent outputs** per ensemble protocol — check that each persona addressed the actual code and stayed coherent.

6. **Pass triaged persona summaries to a synthesis agent** loaded with `/pony-synthesize`, plus the review-specific synthesis focus (below). Provide the paths to each persona's evidence file so the synthesizer can dig in when needed. Instruct the synthesizer to produce its output in the final review format (below) rather than the generic synthesizer format. If this is a re-review (iterative mode), include the full review history: for each prior round, what was found, what was fixed, what was parked. The synthesizer uses this to verify fixes, avoid re-flagging parked items, and detect convergence failures.

7. **Reviewer loop on the synthesis** — the reviewer verifies that no persona findings were dropped, severity changes from individual findings are justified, and cross-persona patterns were correctly identified.

8. **Present the consolidated review.**

## Iterative Workflow (Full Mode, Integrated)

When pony-code-review runs as part of the pre-PR pipeline, findings go back to the implementer for triage and fixing. The loop repeats until clean.

### Finding Triage

The implementer categorizes each finding. Every finding must be categorized — no finding is silently dropped, regardless of severity.

- **Fix**: The right action is obvious from the finding itself. Bugs, missing tests, stale docs, pattern violations, naming issues. Fix without waiting for the human.
- **Park**: The finding needs the human's input. Design questions, principle tensions, ambiguous tradeoffs where reasonable people could disagree. Also park findings you disagree with — don't dismiss them. Parked items are listed in the PR for the human to weigh in on.
- **Out of scope**: The finding is real but exists in code that isn't part of the current change. Don't fix it in this PR — file a GitHub issue to track it. Before filing, search existing issues to avoid duplicates. The issue should include the finding, its location, the evidence, and which persona(s) flagged it. These issues ensure that problems discovered during review are tracked even when they can't be addressed in the current change.

### Re-review After Fixes

After fixing the "fix" items, pony-code-review runs again with two key rules:

- **Personas run ignorant.** No knowledge of the prior review. Fresh eyes on all the code, including the fixes. This prevents tunnel-vision on whether prior findings were addressed and ensures the fixes themselves get the same scrutiny as any other code.
- **Synthesis knows the full review history.** The orchestrator passes the complete review history to the synthesis step — not just the immediately prior round, but all prior rounds. For each round: what was found, what was fixed, what was parked. The synthesizer uses this to verify fixes were actually addressed (not just differently broken), avoid re-flagging parked items that the human hasn't ruled on yet, detect whether a fix introduced a new problem that the ignorant personas caught independently, and detect convergence failures (see below).

### Convergence Failure Detection

The synthesizer monitors the review history for signs that point fixes aren't converging — that the code area has a structural problem no amount of individual fixes will resolve. Signals:

- **Recurring location**: The same file or code area produces findings across multiple review rounds, even after fixes are applied. The specific findings may differ each round, but the area keeps generating problems.
- **Rising fix complexity**: Fixes that add complexity (new fields, new branches, new state distinctions, new special cases) rather than simplifying. Each fix makes the next bug harder to see.
- **Bug class repetition**: Multiple findings across rounds that are different symptoms of the same underlying mismatch — e.g., boundary confusion, impedance mismatch between a data structure and its usage pattern, a leaky abstraction that keeps leaking in new places.

When the synthesizer detects a convergence failure, it escalates a structural question: "This area has produced findings across N review rounds. The fixes are adding complexity rather than removing it. Is the underlying data structure / abstraction / design right for this problem?" This is always parked — it's a design decision, not something the implementer resolves autonomously.

The structural question should be specific: name the data structure or abstraction, describe the pattern of bugs it's producing, and suggest what kind of replacement might eliminate the bug class. Don't just say "consider a redesign" — say "the radix tree is producing segment-boundary bugs because it operates at the character level; a segment-level trie would eliminate this class structurally."

### Loop Termination

The loop ends when no findings remain except parked and out-of-scope items. At that point, open the PR with the parked items listed in the PR description or as a PR comment so the human can weigh in — never in commit messages. Commit messages are for change rationale only; parked items are transient review artifacts that don't belong in git history. If the human's direction on parked items requires changes, make them and run a final pony-code-review pass to confirm.

## Process: Lightweight Mode

Lightweight mode runs 3 personas in a single pass with no iterative re-review. Load `/pony-ensemble` for the mechanical process.

### Personas

**Core pair (always run):**

| File | Focus |
|------|-------|
| `correctness.md` | Logic, edge cases, completeness for valid inputs |
| `adversarial.md` | Concrete break scenarios, backward from failure |

**Context-dependent slot (pick 1):**

| When | Pick |
|------|------|
| Tests changed or should have been changed | `tests.md` |
| API surface changed | `api-design.md` |
| Change touches trust boundaries or external input | `security.md` |
| Change is on a hot path or introduces coordination points | `performance.md` |

Pick whichever is most relevant to the change. If multiple conditions apply, pick the most relevant one. If the reason for picking a particular persona is a change characteristic that also appears in the full-mode selection criteria, that's a signal the change warrants full mode — don't use the persona pick to compensate for a wrong mode selection.

**Not included in lightweight:**

- **Principles** — a fresh-context principle check adds diminishing value on small changes. If the change is large enough to benefit from it, it's large enough for full mode.
- **Wildcard** — the wildcard's value scales with change complexity and the number of other personas whose territory it needs to look beyond. With only 3 focused personas on a small change, there's insufficient covered territory for the wildcard to add meaningful signal.

### Steps

1. **Identify the review target.** Same as full mode — PR URL, branch name, or local changes. Resolve into concrete diff instructions for agents.

2. **Build and run tests once.** Same as full mode — capture output, proceed with review even if build or tests fail.

3. **Create a temporary directory for evidence files.** Use `~/tmp/code-review-<timestamp>/`. Same convention as full mode.

4. **Spawn 3 persona agents in parallel** as Tasks with subagent_type="general-purpose" and model="opus". Each agent's prompt includes:

   - The persona document, read from the corresponding file in `personas/`. When a persona's context loading references an external skill (e.g., `/pony-test-design`, `/pony-pbt-patterns`, `/pony-ref`), read that skill's content and include it in the agent prompt.
   - The code-review principles: read `references/principles.md` (alongside this skill) and include its content in the agent prompt, the same way referenced skills are injected above. Also instruct the agent to read the project `CLAUDE.md` if one exists (not all projects have one; if absent, note it and proceed) and to follow its conventions, including loading any skills it references.
   - The review target: base branch, diff command, PR URL, and any related issue/discussion URLs.
   - Instructions to read all changed files in full (not just diffs), plus supporting files needed for context.
   - The captured build output and test results from step 2 — always provided to Correctness and Adversarial. Also provided to Tests when it is the context-dependent persona.
   - The shared persona output format (below), including the evidence file path and instructions to write detailed evidence to that file and return a summary.
   - Instructions to run a reviewer loop before returning — the reviewer checks the persona's analysis for coherence, completeness, and evidence quality, not the underlying code a second time.
   - Instructions that this is an ensemble agent — return findings to the orchestrator, don't take external actions.

   When the review target is a fix, the Adversarial persona's prompt still includes the fix-specific focus from the ensemble protocol: construct a concrete scenario where the bug still occurs despite the fix.

   The Wildcard-specific instruction (providing other personas' identity statements) does not apply — Wildcard is not part of lightweight mode.

5. **Triage agent outputs** per ensemble protocol — check that each persona addressed the actual code and stayed coherent.

6. **Pass triaged persona summaries to a synthesis agent** loaded with `/pony-synthesize`, plus the lightweight synthesis focus (below). Provide the paths to each persona's evidence file so the synthesizer can dig in when needed. Instruct the synthesizer to produce its output in the final review format (below) rather than the generic synthesizer format — same override as full mode.

7. **Reviewer loop on the synthesis** — same checks as full mode: verify no persona findings were dropped, severity changes from individual findings are justified, and cross-persona patterns were correctly identified.

8. **Present the consolidated review** in the same output format as full mode.

### Finding Triage (Lightweight, Integrated)

Same categories as full mode:

- **Fix**: Obvious action from the finding itself. Fix without waiting.
- **Park**: Needs the human's input. Listed in the PR.
- **Out of scope**: Real but in code outside this change. File a GitHub issue.

No re-review loop. Fix the findings and proceed to opening the PR.

If the review produces an unexpectedly high density of findings relative to the change size, if a finding reveals the approach is fundamentally wrong, or if a finding reveals the change touches more subsystems or has more complex interactions than the mode selection assumed, the orchestrator presents this to the human. The human decides what to do — run full mode from scratch, fix directly, rethink the approach, or something else. Lightweight doesn't prescribe the response; it presents the information.

## Synthesis Focus: Full Mode

The synthesizer should pay special attention to:

- **Severity conflicts**: When one persona flags something as critical and another doesn't mention it, investigate why. The persona that flagged it may have domain-specific knowledge the others lack. Don't average severity — if one reviewer says "critical" with evidence, the finding is critical.
- **Pattern detection**: Multiple low-severity findings in the same area of code often indicate a structural problem. Five small issues is one design issue. Look for clusters.
- **Adversarial findings the correctness reviewer missed**: These are high-value — the correctness reviewer was looking forward from the code and didn't see the failure path.
- **Test gaps matching other findings**: When the Tests persona identifies coverage gaps that align with issues found by Adversarial or Correctness, those are the highest-priority test additions.
- **Principle violations others missed**: Findings from the Principles persona that no other persona noticed represent systematic blind spots.
- **Cross-persona corroboration**: When multiple personas independently flag the same issue from different angles, that's high confidence. Call it out.
- **Wildcard findings**: The wildcard persona deliberately looks for things the other personas miss. Its findings may be unconventional — evaluate them on merit, not on whether they fit a category. If a wildcard finding aligns with a faint signal from another persona, that's strong evidence both caught the same thing from different angles.
- **Convergence failures** (re-reviews only): Check the review history for signs that an area isn't converging — recurring findings in the same location, fixes that add complexity instead of removing it, different symptoms of the same structural mismatch across rounds. When detected, escalate a specific structural question (see "Convergence Failure Detection" in the iterative workflow section). This is always a parked item.
- **Pre-existing issues**: Findings about problems in code outside the current change are still findings — never silently discard them. Flag them clearly as pre-existing so the implementer can triage them as "out of scope" and file issues. A review that discovers a real problem and then drops it because "it's not part of this PR" has wasted the discovery.
- **When digging deeper**: Work from the summaries by default. Read the evidence files when a finding needs more context — when severities conflict, when a finding's summary is ambiguous, or when you need to verify the evidence supports the claim.

## Synthesis Focus: Lightweight Mode

The synthesizer should pay special attention to:

- **Severity conflicts**: Same as full mode — when one persona flags something as critical and another doesn't mention it, investigate why. Don't average severity.
- **Adversarial findings the correctness reviewer missed**: These are high-value — the correctness reviewer was looking forward from the code and didn't see the failure path.
- **Cross-persona corroboration**: When multiple personas independently flag the same issue from different angles, that's high confidence.
- **Test gaps matching other findings**: When Tests is the context-dependent persona and identifies coverage gaps that align with issues found by Adversarial or Correctness, those are the highest-priority test additions.
- **Pre-existing issues**: Same as full mode — never silently discard them. Flag as pre-existing for "out of scope" triage.
- **Finding density signal**: If the 3 personas collectively produce more findings than expected for the change size, note this explicitly. A high density of findings on a small change suggests the change is more complex than it appeared and may warrant full mode. This is the synthesizer's primary escalation signal.
- **When digging deeper**: Same as full mode — summaries by default, evidence files when needed.

## Final Output Format

Findings grouped by severity, then by location:

**Critical** (must fix before merge)
**High** (should fix — real risk if left)
**Medium** (would improve the code, not blocking)
**Low** (suggestions, style)

Each finding:
- **Location**: `file:line`
- **Finding**: What's wrong
- **Personas**: Which reviewer(s) flagged this
- **Evidence**: What was observed
- **Suggested fix**: If applicable

Followed by:
- **Passes**: Key things checked across all personas that look correct (brief — builds confidence the review was thorough)
- **Uncertainties**: Things that need input — genuinely hard questions no persona could resolve

## Shared Persona Output Format

Include these instructions in every persona agent's prompt.

Each persona produces two artifacts:

### Evidence File

Written to the file path provided by the orchestrator. Contains the full detailed analysis: every finding with complete evidence, full code excerpts, detailed reasoning, complete pass/fail evaluations. This is the authoritative record.

### Summary (returned to orchestrator)

A structured summary for the synthesizer to work from:

**Findings** — ordered by severity (Critical > High > Medium > Low). Each:
- **Location**: `file:line`
- **Severity**: Critical / High / Medium / Low
- **Confidence**: High / Medium / Low
- **Finding**: What's wrong (concise — full evidence is in the file)
- **Suggested fix**: If applicable

Confidence calibration: **High** = verified by reading code or running tests. **Medium** = strong inference from code structure, not directly verified. **Low** = inferred from patterns or conventions, may not apply.

**Passes** — key things checked that look correct. Brief.

**Uncertainties** — things the persona couldn't determine, and why.

## Personas

The persona documents are in `personas/`. Full mode uses all 8; lightweight uses Correctness + Adversarial + one context-dependent persona (see "Process: Lightweight Mode" for selection criteria).

| File | Focus |
|------|-------|
| `correctness.md` | Logic, edge cases, completeness for valid inputs |
| `adversarial.md` | Concrete break scenarios, backward from failure |
| `api-design.md` | Consumer experience, naming, footguns, pattern conformance |
| `security.md` | Trust boundaries, injection, auth, resource bounds |
| `performance.md` | Architectural bottlenecks, then local waste |
| `tests.md` | Test quality, missing tests, counterfactual reasoning |
| `principles.md` | Systematic principles audit with evidence |
| `wildcard.md` | Chaos agent — finds what the others miss |
