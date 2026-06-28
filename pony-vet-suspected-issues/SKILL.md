---
name: pony-vet-suspected-issues
description: How to handle a problem you spot while working on something else — capture it as a suspected issue instead of filing on the spot, then after the current PR is open, vet each one (verify, scope, review) and file a correct issue or discard it. Load when you find an incidental, out-of-scope problem mid-task, when a code or docs review surfaces an out-of-scope finding, or when the PR is open and you have suspected issues to work through.
disable-model-invocation: false
---

# Vet Suspected Issues

When you spot a problem in code or documentation that is outside the change you are working on, do not file an issue for it on the spot. Write it down as a suspected issue and keep going. After the current PR is open, vet each one — verify it, scope it, review it — and only then file an issue, or discard it with a reason.

The reason for the deferral: issues filed on the spot are often wrong or incomplete. You file them from a single observation while loaded on the work at hand, without confirming the problem holds, finding its real scope, searching for duplicates, or reviewing the issue itself. Moving the work to a phase with full attention and real verification is what makes the issue correct.

## Where suspected issues come from

Two sources:

- **You notice something while working** — an unrelated bug, a stale comment, a gap — in code or docs that is not part of your change.
- **A review surfaces an out-of-scope finding** — `pony-code-review` and `pony-docs-review` route findings that are real but live outside the current change here, instead of filing them mid-review. These arrive with the persona's evidence and which persona flagged it. That evidence is the starting point for vetting, not a finished issue.

## Suspected issues are not parked items

Keep the two apart. A **parked item** is a decision that needs the human's input on the current change; it waits for the human and is listed in the PR. A **suspected issue** is a problem outside the current change that you vet yourself and then file or discard.

## Capture (while working)

When you notice an out-of-scope problem, do not investigate it and do not file it. Add it to a suspected-issue list and keep moving. Each entry records enough to vet it later without rediscovering it:

- What you saw, and where (`file:line`).
- What you were doing when you noticed it.
- Your initial hypothesis — marked as a hypothesis, not a conclusion.

Capture bar: a concrete problem you can point at. A vague "this could be nicer" does not go on the list.

Keep the list with the working session, alongside whatever you are already tracking for the current change. When the PR opens, surface the open suspected issues so the vetting phase works from them and a long session doesn't lose them.

## Vet (after the current PR is open)

Run this after the current PR is open, as its own closing phase — not while the main work is in flight. It is not a side quest. (If a suspected issue turns out to be part of the current change after all, it stops being one and folds into that work instead.)

Lock down each suspected issue. Default to the lightweight path; escalate when one is bigger than it looked.

1. **Verify it's real.** Spawn a fresh-context agent. Give it the suspected issue — the observation, the location, your hypothesis — and have it read the actual code and judge whether the problem is real, from evidence rather than argument. For a behavioral bug, verifying means reproducing it (load `pony-debug`). If the suspected issue came from a review persona, you already have its evidence: confirm it still holds and build on it, rather than re-deriving the finding from scratch. Outcomes:
   - **Confirmed** — continue.
   - **Not a problem** — discard it and record why. This is a real outcome, not a failure. It is the wrong issue caught before it ships.
   - **Needs more information** — dig until you can confirm or discard.
2. **Find the true scope and root cause.** One instance or a pattern? What is the actual extent? A premature issue describes one symptom; vetting finds the whole shape. This is what stops issues from missing points.
3. **Check for duplicates.** Search the existing issues so you do not file one that is already there.
4. **Draft the issue.** Follow the project's issue conventions. Keep the body about the problem itself — the symptom, where it lives, the evidence, the scope — not about the review or how the issue came to be filed. Set whatever issue type or labels the project uses.
5. **Review the draft.** A fresh-context reviewer checks that the claim holds, the scope is right, and nothing is missing. This is the direct fix for issues that miss points.
6. **File it.**

**Escalate** from the lightweight path to a heavier review when a suspected issue turns out to be a pattern across the codebase or a design problem rather than a single bug — load `pony-code-review` for code, `pony-software-design` for a design problem.

If vetting a suspected issue surfaces a question that is the human's to decide — a design call, an ambiguous tradeoff — it stops being a suspected issue and becomes a parked item for the human, rather than being forced into an issue.

**Fast path:** a problem with nothing behavioral to verify — a typo, a stale comment — skips the reproduction in step 1. Give it a light check and file. Anything that claims a bug or a behavior takes the full path. "It's obviously fine to skip" is exactly the judgment that produces wrong issues.
