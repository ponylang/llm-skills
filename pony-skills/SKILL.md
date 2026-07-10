---
name: pony-skills
description: Routing index for the Pony skills — tells you which pony-* skill to load for each task, and when. Load at the start of work in a Pony project.
disable-model-invocation: false
---

# Pony Skills

When one of these applies, load the named skill.

| When | Load |
|---|---|
| Working on Pony at all — before you start, and for questions about capabilities, the type system, the runtime, or testing | `pony-ref` |
| Writing any prose that ships with the code — a comment, docstring, release note, README, issue, PR description, or commit message | `pony-prose` |
| Before writing or changing a comment or docstring | `pony-comments` |
| Designing APIs, types, features, or system boundaries (not just implementing an existing design) | `pony-software-design` |
| Reviewing code, or before opening a PR | `pony-code-review` |
| Reviewing a documentation-only change | `pony-docs-review` |
| A problem you notice while working on something else — decide whether it belongs in your change, and if not, capture it and vet it before filing an issue | `pony-vet-suspected-issues` |
| Writing tests, or assessing test quality | `pony-test-design` |
| Writing property-based or generative tests | `pony-pbt-patterns` |
| Before forming a hypothesis about a non-trivial bug | `pony-debug` |
| Making a user-facing change in a released project (VERSION is not `0.0.0`) | `pony-release-notes` |
| Writing or updating a library's README | `pony-library-readme` |
| Adding, updating, or reorganizing examples | `pony-examples-readme` |
| Running the ensemble workflow (on request) | `pony-ensemble` |
