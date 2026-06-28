---
name: pony-docs-review
description: Ensemble documentation review with specialized reviewer personas. Has full (8-persona) and lightweight (3-persona) modes. Load when reviewing documentation-only changes where code-focused personas don't apply.
disable-model-invocation: false
---

# Documentation Review

Ensemble documentation review that synthesizes findings from specialized reviewer personas. Has two modes: full (8 personas, iterative re-review) and lightweight (3 personas, single pass). Not for one-line typo fixes or trivial formatting changes — for those, a lightweight self-review is sufficient.

## Mode Selection

The skill has two modes: **full** and **lightweight**. The orchestrator selects the appropriate mode based on the criteria below and proceeds. Report the mode choice when presenting results — the human can request full mode if lightweight was used and they want deeper coverage.

**Full mode** is the default. Use it when:

- The change has non-obvious scope — a new tutorial section, a restructured reference guide, multi-page content changes
- The change touches multiple documentation areas or crosses topic boundaries
- "Is the content right?" is genuinely uncertain — new technical content, changed API descriptions
- The change is large enough that a single review pass might miss interactions between sections

**Lightweight mode** is for small, bounded documentation changes:

- Fixing factual errors in a well-understood area
- Small additions to existing pages following established patterns
- Updating documentation to reflect a code change that's already reviewed
- Single-page changes with clear scope

When in doubt, use full mode. Lightweight is appropriate when the change is clearly bounded — the orchestrator should be able to state what makes it bounded and why fewer personas are sufficient.

Note: the pony-code-review skill follows a similar mode-selection pattern but with code-specific criteria and a different persona roster. Pony-docs-review and pony-code-review are separate skills for separate concerns — documentation review and code review have different failure modes, different severity calibration, and different reviewer lenses.

## Invocation Modes

These modes apply to both full and lightweight:

**Integrated (pre-PR pipeline):** The implementer runs pony-docs-review as part of their pre-PR workflow for documentation-only changes, in place of pony-code-review. In full mode, findings are triaged, unambiguous ones are fixed, and the loop repeats until clean. In lightweight mode, findings are triaged and fixed in a single pass. See the relevant process section below.

**Standalone:** Invoked directly on an existing PR, branch, or local changes for a one-shot documentation review. The process section for the selected mode applies as-is.

## Relationship to Ensemble Workflow

Use the ensemble workflow with documentation-review-specific customizations. Load `pony-ensemble` for the mechanical process. This skill replaces the generic attention focuses with documentation review personas (8 for full mode, 3 for lightweight) and replaces the generic agent output format with the review-specific format defined below.

The ensemble protocol requires an adversarial focus when reviewing fixes. Pony-docs-review does not have a dedicated adversarial persona because documentation "fixes" (correcting factual errors, filling gaps) don't have the same failure mode as code fixes — there's no analog to "the bug still occurs despite the fix." When a pony-docs-review targets a documentation fix, the Accuracy persona naturally covers the adversarial concern: verifying that the corrected information is actually correct and that the fix doesn't introduce new inaccuracies. This satisfies the ensemble protocol's "fix reviews require an adversarial focus" requirement — no additional adversarial agent is needed. The orchestrator should note this in the Accuracy persona's prompt when the review target is a fix.

Persona agents write detailed evidence to files and return structured summaries to the orchestrator. The synthesizer works from summaries and digs into evidence files only when it needs to examine a finding more closely. This prevents context overload during synthesis.

The pony-synthesize skill's output format is not a natural fit for documentation review. The orchestrator instructs the synthesizer to produce output in the review-specific final format (below) rather than the generic synthesizer format. No changes to `pony-synthesize` itself.

## Process: Full Mode

1. **Identify the review target.** PR URL, branch name, or local changes. If not specified, ask. Resolve the target into concrete instructions for agents: the base branch to diff against, the git diff command or `gh pr diff` command to run, and any design doc or issue URLs for context.

2. **Gather context.** Read the documentation being changed in full. Identify:
   - Source code referenced by the documentation (APIs described, code examples shown) — read it
   - Existing related documentation in the same doc set (for consistency and cross-reference checking)
   - Any style guides, documentation conventions, or terminology standards

   At minimum, gather and distribute: Accuracy gets source code, Consistency gets related docs, Principles gets style guides. Each persona's context loading section specifies additional context needs — check them when building prompts. All personas get the full changed documentation.

3. **Create a temporary directory for evidence files.** Use `~/tmp/pony-docs-review-<timestamp>/`. Each persona will write its detailed evidence to a file in this directory. Generate the file path for each persona (e.g., `accuracy-evidence.md`) and pass it in the prompt.

4. **Spawn 8 persona agents in parallel**, each as a fresh-context sub-agent using your most capable model. Each agent's prompt includes:

   - The persona document, read from the corresponding file in `personas/`. When a persona's context loading references an external skill (e.g., `pony-ref`), read that skill's content and include it in the agent prompt.
   - The documentation principles: read `references/principles.md` (alongside this skill) and include its content in the agent prompt, the same way referenced skills are injected above. Also instruct the agent to read the project AGENTS.md if one exists (not all projects have one; if absent, note it and proceed) and to follow its conventions, including loading any skills it references.
   - The review target: base branch, diff command, PR URL, and any related issue/discussion URLs.
   - Instructions to read all changed files in full (not just diffs), plus supporting files needed for context.
   - Relevant gathered context from step 2, distributed to the personas that consume it (e.g. source code for Accuracy; related docs or style guides for Consistency or Principles when they run).
   - The shared persona output format (below), including the evidence file path and instructions to write detailed evidence to that file and return a summary.
   - Instructions to run a reviewer loop before returning — the reviewer checks the persona's analysis for coherence, completeness, and evidence quality, not the documentation a second time.
   - Instructions that this is an ensemble agent — return findings to the orchestrator, don't take external actions.

   **For the Wildcard persona specifically:** include the identity statement (first paragraph) from each of the other 7 personas so the wildcard knows what territory is already covered.

5. **Triage agent outputs** per ensemble protocol — check that each persona addressed the actual documentation and stayed coherent.

6. **Pass triaged persona summaries to a synthesis agent** loaded with `pony-synthesize`, plus the pony-docs-review-specific synthesis focus (below). Provide the paths to each persona's evidence file so the synthesizer can dig in when needed. Instruct the synthesizer to produce its output in the final review format (below) rather than the generic synthesizer format. If this is a re-review (iterative mode), include the full review history: for each prior round, what was found, what was fixed, what was parked. The synthesizer uses this to verify fixes were addressed, avoid re-flagging parked items, and detect convergence failures.

7. **Reviewer loop on the synthesis** — the reviewer verifies that no persona findings were dropped, severity changes from individual findings are justified, and cross-persona patterns were correctly identified.

8. **Present the consolidated review.**

## Iterative Workflow (Full Mode, Integrated)

When pony-docs-review runs as part of the pre-PR pipeline, findings go back to the implementer for triage and fixing. The loop repeats until clean.

### Finding Triage

The implementer categorizes each finding. Every finding must be categorized — no finding is silently dropped, regardless of severity.

- **Fix**: The right action is obvious from the finding itself. Factual errors, broken examples, missing steps, stale cross-references, terminology inconsistencies. Fix without waiting.
- **Park**: The finding needs the maintainer's input. Tone questions, scope decisions, audience disagreements, ambiguous tradeoffs where reasonable people could disagree. Also park findings you disagree with — don't dismiss them. Parked items are listed in the PR for the maintainer to weigh in on.
- **Out of scope**: The finding is real but exists in documentation that isn't part of the current change. Don't fix it in this PR, and don't file an issue for it on the spot. Capture it as a suspected issue — carry the finding, its location, the evidence, and which persona(s) flagged it — and vet it after this PR is open before filing: confirm it still holds, find its real scope, check for duplicates, and review the draft. Load `pony-vet-suspected-issues` for the procedure. Filing straight from a review tends to produce issues that are wrong or miss the real scope; the persona's evidence is the starting point for vetting, not the finished issue.

### Re-review After Fixes

After fixing the "fix" items, pony-docs-review runs again with two key rules:

- **Personas run ignorant.** No knowledge of the prior review. Fresh eyes on all the documentation, including the fixes. This prevents tunnel-vision on whether prior findings were addressed and ensures the fixes themselves get the same scrutiny as any other content.
- **Synthesis knows the full review history.** The orchestrator passes the complete review history to the synthesis step — not just the immediately prior round, but all prior rounds. For each round: what was found, what was fixed, what was parked. The synthesizer uses this to verify fixes were actually addressed (not just differently wrong), avoid re-flagging parked items that the maintainer hasn't ruled on yet, detect whether a fix introduced a new problem that the ignorant personas caught independently, and detect convergence failures (see below).

### Convergence Failure Detection

The synthesizer monitors the review history for signs that point fixes aren't converging — that the documentation area has a structural problem no amount of individual fixes will resolve. Signals:

- **Recurring location**: The same section or page produces findings across multiple review rounds, even after fixes are applied. The specific findings may differ each round, but the area keeps generating problems.
- **Rising fix complexity**: Fixes that add complexity (more caveats, more qualifications, more conditional language) rather than clarifying. Each fix makes the prose harder to follow.
- **Problem class repetition**: Multiple findings across rounds that are different symptoms of the same underlying issue — e.g., a section that keeps producing findings because it's trying to explain something the reader doesn't have the background for yet, or a page that mixes two audiences and keeps failing for one of them.

When the synthesizer detects a convergence failure, it escalates a structural question: "This section has produced findings across N review rounds. The fixes are adding qualifications rather than clarifying. Is the underlying organization / audience targeting / conceptual framework right for this content?" This is always parked — it's a structural decision, not something the implementer resolves autonomously.

The structural question should be specific: name the section, describe the pattern of findings it's producing, and suggest what kind of restructuring might eliminate the finding class. Don't just say "consider rewriting" — say "this section is trying to teach concept X before the reader has concept Y; moving section 3 before section 2 would eliminate this class of completeness findings."

### Loop Termination

The loop ends when no findings remain except parked and out-of-scope items (the out-of-scope findings are held as suspected issues to vet after the PR, not filed now — see the triage above). At that point, open the PR with the parked items listed in the PR description or as a PR comment so the maintainer can weigh in — never in commit messages. Commit messages are for change rationale only; parked items are transient review artifacts that don't belong in git history. If the maintainer's direction on parked items requires changes, make them and run a final pony-docs-review pass to confirm.

## Process: Lightweight Mode

Lightweight mode runs 3 personas in a single pass with no iterative re-review. Load `pony-ensemble` for the mechanical process.

### Personas

**Core pair (always run):**

| File | Focus |
|------|-------|
| `accuracy.md` | Technical correctness — cross-references claims against source code |
| `completeness.md` | Coverage gaps — missing prerequisites, skipped steps, unstated assumptions |

**Context-dependent slot (pick 1):**

| When | Pick |
|------|------|
| Tutorial, getting-started, or guide content | `reader-experience.md` |
| Reference documentation or API docs | `consistency.md` |
| Large document or multi-page change | `structure.md` |
| Established style guide applies | `principles.md` |

Pick whichever is most relevant to the change. If multiple conditions apply, pick the most relevant one. If the reason for picking a particular persona is a change characteristic that also appears in the full-mode selection criteria, that's a signal the change warrants full mode — don't use the persona pick to compensate for a wrong mode selection. If none of the conditions clearly apply, the change may be simple enough to skip pony-docs-review and rely on a lightweight self-review alone.

**Not included in lightweight:**

- **Clarity** — important but lower severity than accuracy/completeness; unclear writing can be re-read, wrong or missing information can't be worked around. If the change is large enough to benefit from a dedicated clarity pass, it's large enough for full mode.
- **Wildcard** — the wildcard's value scales with change complexity and the number of other personas whose territory it needs to look beyond. With only 3 focused personas on a small change, there's insufficient covered territory for the wildcard to add meaningful signal.

### Steps

1. **Identify the review target.** Same as full mode — PR URL, branch name, or local changes. Resolve into concrete diff instructions for agents.

2. **Gather context.** Same as full mode — read changed documentation in full, identify referenced source code, related docs, and style guides.

3. **Create a temporary directory for evidence files.** Use `~/tmp/pony-docs-review-<timestamp>/`. Same convention as full mode.

4. **Spawn 3 persona agents in parallel**, each as a fresh-context sub-agent using your most capable model. Each agent's prompt includes:

   - The persona document, read from the corresponding file in `personas/`. When a persona's context loading references an external skill, read that skill's content and include it in the agent prompt.
   - The documentation principles: read `references/principles.md` (alongside this skill) and include its content in the agent prompt, the same way referenced skills are injected above. Also instruct the agent to read the project AGENTS.md if one exists (not all projects have one; if absent, note it and proceed) and to follow its conventions, including loading any skills it references.
   - The review target: base branch, diff command, PR URL, and any related issue/discussion URLs.
   - Instructions to read all changed files in full (not just diffs), plus supporting files needed for context.
   - Relevant gathered context from step 2, distributed to the personas that consume it (e.g. source code for Accuracy; related docs or style guides for Consistency or Principles when they run).
   - The shared persona output format (below), including the evidence file path and instructions to write detailed evidence to that file and return a summary.
   - Instructions to run a reviewer loop before returning — the reviewer checks the persona's analysis for coherence, completeness, and evidence quality, not the documentation a second time.
   - Instructions that this is an ensemble agent — return findings to the orchestrator, don't take external actions.

   When the review target is a fix, the Accuracy persona's prompt includes the fix-specific focus: verify that the corrected information is actually correct and that the fix doesn't introduce new inaccuracies.

   The Wildcard-specific instruction (providing other personas' identity statements) does not apply — Wildcard is not part of lightweight mode.

5. **Triage agent outputs** per ensemble protocol — check that each persona addressed the actual documentation and stayed coherent.

6. **Pass triaged persona summaries to a synthesis agent** loaded with `pony-synthesize`, plus the lightweight synthesis focus (below). Provide the paths to each persona's evidence file so the synthesizer can dig in when needed. Instruct the synthesizer to produce its output in the final review format (below) rather than the generic synthesizer format — same override as full mode.

7. **Reviewer loop on the synthesis** — same checks as full mode: verify no persona findings were dropped, severity changes from individual findings are justified, and cross-persona patterns were correctly identified.

8. **Present the consolidated review** in the same output format as full mode.

### Finding Triage (Lightweight, Integrated)

Same categories as full mode:

- **Fix**: Obvious action from the finding itself. Fix without waiting.
- **Park**: Needs the human's input. Listed in the PR.
- **Out of scope**: Real but in documentation outside this change. Capture it as a suspected issue and vet it after the PR before filing — load `pony-vet-suspected-issues`; don't file on the spot.

No re-review loop. Fix the findings and proceed to opening the PR.

If the review produces an unexpectedly high density of findings relative to the change size, if a finding reveals the content is fundamentally wrong, or if a finding reveals the change touches more documentation areas or has more complex interactions than the mode selection assumed, the orchestrator presents this to the human. The human decides what to do — run full mode from scratch, fix directly, rethink the approach, or something else. Lightweight doesn't prescribe the response; it presents the information.

## Synthesis Focus: Full Mode

The synthesizer should pay special attention to:

- **Severity conflicts**: When one persona flags something as critical and another doesn't mention it, investigate why. The persona that flagged it may have domain-specific knowledge the others lack. Don't average severity — if one reviewer says "critical" with evidence, the finding is critical.
- **Accuracy findings other personas missed**: These are high-value — technically wrong content that passed clarity, structure, and completeness checks. The other personas were evaluating the documentation as prose; only Accuracy cross-referenced it against reality.
- **Completeness + Reader Experience alignment**: When both flag the same gap from different angles (Completeness: "step 3 is missing"; Reader Experience: "a reader would get stuck here"), that's the highest-priority addition.
- **Clarity clusters**: Multiple clarity findings in the same section suggest the section needs restructuring, not sentence-level fixes. Escalate to a structural observation.
- **Cross-persona corroboration**: When multiple personas independently flag the same issue from different angles, that's high confidence. Call it out.
- **Wildcard findings**: The wildcard persona deliberately looks for things the other personas miss. Its findings may be unconventional — evaluate them on merit, not on whether they fit a category. If a wildcard finding aligns with a faint signal from another persona, that's strong evidence both caught the same thing from different angles.
- **Convergence failures** (re-reviews only): Check the review history for signs that an area isn't converging — recurring findings in the same section, fixes that add complexity instead of clarifying, different symptoms of the same structural issue across rounds. When detected, escalate a specific structural question (see "Convergence Failure Detection" in the iterative workflow section). This is always a parked item.
- **Pre-existing issues**: Findings about problems in documentation outside the current change are still findings — never silently discard them. Flag them clearly as pre-existing so the implementer can triage them as "out of scope" and capture them as suspected issues to vet after the PR. A review that discovers a real problem and then drops it because "it's not part of this PR" has wasted the discovery.
- **When digging deeper**: Work from the summaries by default. Read the evidence files when a finding needs more context — when severities conflict, when a finding's summary is ambiguous, or when you need to verify the evidence supports the claim.

## Synthesis Focus: Lightweight Mode

The synthesizer should pay special attention to:

- **Severity conflicts**: Same as full mode — when one persona flags something as critical and another doesn't mention it, investigate why. Don't average severity.
- **Accuracy findings the completeness reviewer missed**: These are high-value — the content was there but wrong.
- **Cross-persona corroboration**: When multiple personas independently flag the same issue from different angles, that's high confidence.
- **Context-dependent persona alignment**: When the context-dependent persona's findings align with Accuracy or Completeness findings, those are the highest-priority items.
- **Pre-existing issues**: Same as full mode — never silently discard them. Flag as pre-existing for "out of scope" triage.
- **Finding density signal**: If the 3 personas collectively produce more findings than expected for the change size, note this explicitly. A high density of findings on a small change suggests the change is more complex than it appeared and may warrant full mode. This is the synthesizer's primary escalation signal.
- **When digging deeper**: Same as full mode — summaries by default, evidence files when needed.

## Severity Calibration

- **Critical** (must fix before merge): Technically incorrect information that would cause harm — wrong commands that could damage a system, incorrect security guidance, code examples that produce wrong results
- **High** (should fix — real risk if left): Missing critical information that would leave readers stuck, misleading content that leads to wrong conclusions, broken code examples
- **Medium** (would improve the docs, not blocking): Clarity issues that slow comprehension, structural problems that make information hard to find, inconsistencies between documents
- **Low** (suggestions, style): Formatting, minor wording improvements, suggestions

## Final Output Format

Findings grouped by severity, then by location:

**Critical** (must fix before merge)
**High** (should fix — real risk if left)
**Medium** (would improve the docs, not blocking)
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

Written to the file path provided by the orchestrator. Contains the full detailed analysis: every finding with complete evidence, full text excerpts, detailed reasoning, complete pass/fail evaluations. This is the authoritative record.

### Summary (returned to orchestrator)

A structured summary for the synthesizer to work from:

**Findings** — ordered by severity (Critical > High > Medium > Low). Each:
- **Location**: `file:line`
- **Severity**: Critical / High / Medium / Low
- **Confidence**: High / Medium / Low
- **Finding**: What's wrong (concise — full evidence is in the file)
- **Suggested fix**: If applicable

Confidence calibration: **High** = verified by reading source code, checking cross-references, or demonstrating a specific misreading (e.g., constructing an alternative interpretation of an ambiguous sentence). **Medium** = strong inference from document structure or content, not directly verified. **Low** = inferred from patterns or conventions, may not apply.

**Passes** — key things checked that look correct. Brief.

**Uncertainties** — things the persona couldn't determine, and why.

## Personas

The persona documents are in `personas/`. Full mode uses all 8; lightweight uses Accuracy + Completeness + one context-dependent persona (see "Process: Lightweight Mode" for selection criteria).

| File | Focus |
|------|-------|
| `accuracy.md` | Technical correctness — cross-references claims against source code |
| `completeness.md` | Coverage gaps — missing prerequisites, skipped steps, unstated assumptions |
| `clarity.md` | Language quality — ambiguity, jargon, unclear antecedents |
| `structure.md` | Organization and flow — information architecture, concept ordering, findability |
| `consistency.md` | Internal and external consistency — terminology, formatting, cross-references |
| `reader-experience.md` | End-to-end journey — can the audience achieve their goal? |
| `principles.md` | Systematic check against documentation conventions and principles |
| `wildcard.md` | Chaos agent — finds what the others miss |
