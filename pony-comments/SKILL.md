---
name: pony-comments
description: What earns a comment, what never belongs in one, and what to do when two distant things must change together. Load before writing or changing any comment or docstring. Language-agnostic.
disable-model-invocation: false
---

# Comments

A comment is forever. The code around it moves, the tests move, the build moves, and the comment stays exactly as written with nothing to tell you it started lying. Comments have no tests. Write accordingly.

Load `pony-prose` first: it is the rulebook for how the words read, in a comment or anywhere else. This skill is the rulebook for what earns a comment at all. The editor persona in `pony-code-review` checks changed prose against both.

## Default: don't

Most comments restate the line beneath them, and the line already said it. Before writing one, try renaming the thing instead. A better name is a comment that cannot go stale.

Write a comment only when a future reader would re-derive it after a debugging session. That is the bar, and most comments do not clear it.

## Never write a fact with a shelf life

A comment outlives the machinery around it. These all rot:

- what CI runs, and which suite covers a case
- whether a test exists — "nothing catches this," "no test covers this," "verified by reasoning"
- what a build does today — "a normal build doesn't build the tool tests"
- a version — "as of 0.3," "since the rewrite"

Every one becomes false the moment somebody edits a workflow or deletes a test, and nothing catches it.

Run this check before you write, not after. It costs nothing:

> If deleting a test or editing a workflow would make this sentence false, it does not belong in a comment.

The information is still worth having. It belongs where the machinery is documented and maintained: the build file, the CI config, the project's `AGENTS.md`.

One word needs care. "Silently" is a fact about the program when it means the code produces a wrong value and raises nothing. It is a shelf-life claim when it means no test catches it. Only the first belongs in a comment.

## A comment exists to explain

One that doesn't is worse than none — it costs the reader effort and returns nothing. The plainness rules that keep a comment legible, including never coining jargon for what the code does, live in `pony-prose`; load it before writing one.

## Never narrate history

"Previously this returned -1." "Before the refactor we…" "Added in 0.3." Version control remembers. The next reader does not need it inline.

## Never leave dead status prose

`// WIP`. A `// TODO: add validation` after validation exists. Dated notes. Apologetic stubs. Commented-out code. Section banners the code structure already conveys — a banner survives only when it marks something the structure cannot, like a "do not reorder" boundary.

## Never list your callers

A thing being used does not need to name who uses it. When the caller names the callee — a call, an import, an include — that reference already records the relationship, and the toolchain follows it. A comment inside the callee listing its callers adds a backward link that isn't in the code, that nothing enforces, and that goes stale the moment the caller set changes. Documenting it that way *creates* the problem it claims to document.

Keep such a note only when the comment is the relationship's only record: an external, dynamically dispatched, or convention-matched caller that no in-repo reference names — a cron job, a plugin loaded by name, a format two files must agree on.

## When two distant things must change together

This is where most bad comments come from. "Coupling" sounds important, and writing one down feels like doing the job well. Usually it isn't one.

### What it is

Three things, all true at once:

1. A constraint relates values in two places.
2. A normal edit to one side violates it.
3. Nothing local at either end leads you to the other.

The third is what earns the comment. Standing at one end, you have no way to discover the other exists.

Equality is only one shape the constraint takes:

- an enum's order, and a hand-written table of its numbers in another language
- a struct's layout, and a foreign-function mirror of it
- a heartbeat interval, and the watchdog window that has to stay well above it
- an error message's wording, and the script that greps for a substring of it
- a base image's version, and the package name a release workflow gates on
- a signal the runtime reserves, and the library that must refuse to hand it out

### What it is not

**A call, an import, an include, a shared constant.** These are references. The toolchain follows them and keeps both ends together. If one file includes the header that defines the value, the two cannot drift. Ordinary use of a thing is not a coupling.

**Both ends in the same file.** Local knowledge finds it. If it still needs saying, say it — but it isn't this.

**Anything where breaking it only costs speed.** A cache that gets rebuilt when cold is slower, not wrong. No constraint was violated.

**Reading a field. Calling a function. Implementing an interface.** That is code.

### What to do, in order

**Remove it.** Make the two ends one end. Unify the duplicated predicate. Generate the mirror from its source. Derive one side from the other. A coupling you delete cannot rot, cannot be missed, and needs no comment.

**Pin it.** A static assertion, a generated header, a test whose only job is to fail when the constraint breaks. This turns a value into a reference and hands it to the toolchain, which never forgets.

**Comment both ends.** Only when the first two are genuinely impossible — an FFI boundary between languages, a version string in a container image, a constant two runtimes agree on.

Reach for the comment last. It is what you write when you failed to remove the coupling, not the way to record that you found one.

### What the comment says

Three things, and nothing else:

- where the other end is: file, symbol
- what the constraint is
- what goes wrong when it breaks

Put one at each end. Nothing about tests, nothing about CI, nothing about which suite to run.

Whether the coupling *can* be tested is a real question and a separate one. If it can, test it — that is the second rung. If it cannot, say so to a human in the pull request, where it gets read once and acted on, not in a comment that will outlive the reason.

## Docstrings are different

They are for the people using the thing, not the people maintaining it. Write them fully — "default: don't" does not apply. The rules above about shelf life and history still do, as do all of `pony-prose`'s.

Full does not mean padded. A docstring gives a caller what they need to use the thing correctly: what it does, and the guarantees they can rely on. It says nothing about how it works, and it doesn't restate the signature.

In Pony, `\nodoc\` on test declarations is load-bearing tooling, not prose. Never remove it.

## What earns a comment

For the avoidance of doubt, keep:

- a non-obvious invariant the code cannot express
- the rationale above a conditional or a platform gate, where the *why* is not recoverable from the *what*
- a reference anchor into an external spec, paper, or RFC
- a `TODO` or `FIXME` tied to a live issue
- a coupling comment that reached the third rung
