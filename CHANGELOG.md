# Change Log

All notable changes to this project will be documented in this file. Entries
are grouped by date (UTC) with newest first.

## 2026-07-12

- CHANGED: Treat prose findings as defects, not style suggestions ([PR #63](https://github.com/ponylang/llm-skills/pull/63))

## 2026-07-10

- CHANGED: Rescope what earns a comment to a durable fact, not a body description ([PR #62](https://github.com/ponylang/llm-skills/pull/62))
- ADDED: Add pony-prose, the rulebook for writing prose plainly ([PR #61](https://github.com/ponylang/llm-skills/pull/61))
- CHANGED: Scope a fix to the defect, not to the report ([PR #60](https://github.com/ponylang/llm-skills/pull/60))

## 2026-07-09

- ADDED: Add pony-comments, and make the editor review against it ([PR #59](https://github.com/ponylang/llm-skills/pull/59))
- CHANGED: Make code review comment editor more stringent ([PR #58](https://github.com/ponylang/llm-skills/pull/58))
- CHANGED: Remove the coupling documentation principle ([PR #57](https://github.com/ponylang/llm-skills/pull/57))

## 2026-07-04

- ADDED: Flag coupling comments that don't earn their keep in the code review editor persona ([PR #56](https://github.com/ponylang/llm-skills/pull/56))

## 2026-07-03

- ADDED: Flag invented jargon in the code review editor persona ([PR #55](https://github.com/ponylang/llm-skills/pull/55))

## 2026-06-30

- CHANGED: Added persona to lightweight code review ([PR #54](https://github.com/ponylang/llm-skills/pull/54))

## 2026-06-28

- ADDED: New pony-code-review editor persona ([PR #53](https://github.com/ponylang/llm-skills/pull/53))
- ADDED: Add pony-vet-suspected-issues skill ([PR #52](https://github.com/ponylang/llm-skills/pull/52))

## 2026-06-13

- CHANGED: Clarify literal-path requirement in pony-code-review tmp dir step ([PR #51](https://github.com/ponylang/llm-skills/pull/51))

## 2026-05-22

- ADDED: OpenAI Codex support ([PR #44](https://github.com/ponylang/llm-skills/pull/44))
- ADDED: PDF versions of the pony-ref reference papers ([PR #43](https://github.com/ponylang/llm-skills/pull/43))
- ADDED: Documentation review skill ([PR #41](https://github.com/ponylang/llm-skills/pull/41))

## 2026-05-21

- ADDED: Meta-skill that adds routing for agents to all the skills ([PR #40](https://github.com/ponylang/llm-skills/pull/40))
- FIXED: Improve software design skill performance ([PR #39](https://github.com/ponylang/llm-skills/pull/39))
- FIXED: Bundle pony-code-review's principles instead of reading global CLAUDE.md ([PR #36](https://github.com/ponylang/llm-skills/pull/36))

## 2026-05-20

- ADDED: Incorporate swarm testing techniques into property-based testing skill ([PR #35](https://github.com/ponylang/llm-skills/pull/35))

## 2026-04-07

- CHANGED: Design personas must explore before committing; orchestrator gates quality ([PR #31](https://github.com/ponylang/llm-skills/pull/31))
- FIXED: Skeptic should redirect when subtraction removes everything ([PR #30](https://github.com/ponylang/llm-skills/pull/30))

## 2026-04-04

- CHANGED: Remove pony-ffi-audit skill
- FIXED: Multi-type PR documentation in pony-release-notes ([PR #28](https://github.com/ponylang/llm-skills/pull/28))
- ADDED: pony-debug skill ([PR #21](https://github.com/ponylang/llm-skills/pull/21))
- ADDED: pony-ensemble skill ([PR #18](https://github.com/ponylang/llm-skills/pull/18))
- ADDED: pony-synthesize skill ([PR #18](https://github.com/ponylang/llm-skills/pull/18))
- ADDED: pony-software-design skill ([PR #18](https://github.com/ponylang/llm-skills/pull/18))
- ADDED: pony-test-design skill ([PR #18](https://github.com/ponylang/llm-skills/pull/18))
- ADDED: pony-code-review skill ([PR #18](https://github.com/ponylang/llm-skills/pull/18))
- ADDED: pony-pbt-patterns skill ([PR #18](https://github.com/ponylang/llm-skills/pull/18))

## 2026-04-02

- ADDED: pony-examples-readme skill ([PR #17](https://github.com/ponylang/llm-skills/pull/17))
- ADDED: pony-library-readme skill ([PR #17](https://github.com/ponylang/llm-skills/pull/17))
- ADDED: pony-release-notes skill ([PR #17](https://github.com/ponylang/llm-skills/pull/17))

## 2026-03-14

- FIXED: pony-ref incorrectly stated _method is type-private; it is package-private ([PR #13](https://github.com/ponylang/llm-skills/pull/13))
- FIXED: pony-ref incorrectly stated type aliases can't have docstrings ([PR #13](https://github.com/ponylang/llm-skills/pull/13))

## 2026-03-10

- ADDED: pony-ffi-audit skill ([PR #4](https://github.com/ponylang/llm-skills/pull/4))

## 2026-03-09

- ADDED: pony-ref skill ([PR #2](https://github.com/ponylang/llm-skills/pull/2))
