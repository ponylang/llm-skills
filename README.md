# Pony LLM Skills

Skills for working with [Pony](https://www.ponylang.io) in [Claude Code](https://docs.anthropic.com/en/docs/claude-code). Each skill is a self-contained reference that Claude loads on demand during coding sessions.

## Installation

Clone the repo and run the install script. It symlinks each skill into your Claude Code skills directory so they stay up to date when you pull.

```bash
git clone https://github.com/ponylang/llm-skills.git
cd llm-skills
python install.py
```

That's it. Start a new Claude Code session and the skills are available.

To update later:

```bash
cd llm-skills
git pull
```

No re-install needed — the symlinks point to your clone, so pulling new content updates the skills automatically.

### Uninstalling

Remove the symlinks for each installed skill:

```bash
rm ~/.claude/skills/pony-ref ~/.claude/skills/pony-ffi-audit ~/.claude/skills/pony-examples-readme ~/.claude/skills/pony-library-readme ~/.claude/skills/pony-release-notes
```

This only removes the symlinks, not the cloned repo.

## Skills

### pony-ref

The Pony language reference. Load it with `/pony-ref` at the start of a Pony coding session or when you hit a question about capabilities, the type system, the runtime, or testing.

What's in the quick reference (loaded into context automatically):

- Reference capabilities table, subtyping rules, and key patterns (consume, recover, destructive read)
- Common gotchas (iso aliasing, async stdin, scoping, type aliases)
- Integer arithmetic modes (wrapping, partial, checked)
- Syntax essentials
- PonyCheck property-based testing patterns and gotchas
- Stdlib pitfalls (Reader, Array, Writer, buffered)
- Panic primitives ("mort" pattern)

What's in the `references/` directory (read on demand for deeper questions):

- **Type system synopsis** — distilled from the academic papers. Deny-properties matrix, subtyping lattice, viewpoint adaptation tables, safe-to-write rules, recovery, generics.
- **Runtime/GC synopsis** — ORCA object GC, MAC actor cycle collection, per-actor heaps, causal messaging, the scheduler. Includes an "Implementation Divergences" section documenting where the current ponyc runtime has evolved beyond the papers.
- **Academic papers** — the full text of all nine Pony papers covering the type system, garbage collection, generics, and distributed programming.
- **Website content** — snapshots of the Pony tutorial, patterns cookbook, and main website (via their llms.txt files). Covers language fundamentals, idiomatic patterns, tooling guides, and FAQ.

### pony-ffi-audit

Audit methodology for finding dangerous FFI usage in Pony codebases. Load it with `/pony-ffi-audit` before auditing a project's C-FFI calls for reference capability violations.

Pony's FFI declarations are trusted by the compiler — if you declare a parameter as `tag` but C writes through it, nothing catches the violation at compile time. This skill teaches Claude how to find those gaps systematically.

What's in the quick reference (loaded into context automatically):

- The FFI trust boundary and refcap mutation rules
- Step-by-step audit methodology (find calls, determine mutation, check caps, classify)
- How to identify which arguments a C function mutates (common C functions, OpenSSL, PCRE2, Windows APIs)
- Known patterns: `.cpointer()`/`.cstring()` returning `tag`, structs declared `tag`, FFI-allocated buffers with wrong cap, runtime event handles, finalizer `box`
- Escape hatches: `addressof` and `USize` coercion bypasses
- Fix strategies for each pattern category

What's in the `references/` directory (read on demand):

- **Example audit** — a condensed real-world audit showing the reporting format, classification, and summary structure across multiple projects and all pattern categories.

### pony-examples-readme

Conventions for writing `examples/README.md` files in ponylang projects. Load it with `/pony-examples-readme` when adding, updating, or reorganizing examples.

What's in the quick reference:

- Structure conventions (title, intro paragraph, example entries, category grouping)
- Description format (what it does, what it demonstrates, key concepts)
- Ordering strategies (by complexity, by category, by directory name)
- What to omit (build instructions, source code snippets, detailed setup)

### pony-library-readme

Conventions for writing Pony library project READMEs. Load it with `/pony-library-readme` when writing or updating a library's top-level README.

What's in the quick reference:

- Required sections in order (title, intro, status, installation, API documentation)
- Optional sections (dependencies, usage with inline code examples)
- What ponylang library READMEs deliberately omit (badges, contributing, license, table of contents)

### pony-release-notes

How to write release notes and manage CHANGELOG entries in ponylang projects. Load it with `/pony-release-notes` when writing release notes, updating CHANGELOG, or preparing a PR with user-facing changes.

What's in the quick reference:

- Writing style (user-focused descriptions, dependency bugs as your bugs, breaking change before/after examples)
- Mechanics (`.release-notes/` directory, individual files per PR, CI aggregation)
- Changelog labels (`changelog - fixed`, `changelog - added`, `changelog - changed`)
- Single-type vs. multi-type PR workflows
- Rules for updating accumulated unreleased notes

## Suggested Triggers

Add these to your `CLAUDE.md` or `AGENTS.md` to load skills automatically when relevant:

### /pony-ref

> **Load `/pony-ref` proactively when working on Pony code**: At the start of any conversation where the working directory is a Pony project (contains `corral.json` or `*.pony` files), load `/pony-ref` before doing any work. Also load it mid-conversation when hitting capabilities, type system, runtime, or testing questions.

### /pony-ffi-audit

> **Load `/pony-ffi-audit` before auditing FFI calls**: Load it before auditing a Pony project's C-FFI calls for reference capability violations, mutation through `tag` references, or other FFI trust boundary issues.

### /pony-examples-readme

> **Load `/pony-examples-readme` when working on examples**: Load it when adding, updating, or reorganizing examples in a Pony project, or when writing an `examples/README.md`.

### /pony-library-readme

> **Load `/pony-library-readme` for library READMEs**: Load it when writing or updating a `README.md` for a Pony library project.

### /pony-release-notes

> **Load `/pony-release-notes` for release notes and CHANGELOG**: Load it when writing release notes, updating CHANGELOG, or preparing a PR that includes user-facing changes in a Pony project.
