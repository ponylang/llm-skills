# Pony LLM Skills

Skills for working with [Pony](https://www.ponylang.io) in [Claude Code](https://docs.anthropic.com/en/docs/claude-code). Each skill is a self-contained reference that Claude loads on demand during coding sessions.

**About the `pony-` prefix:** All skills in this repo use a `pony-` prefix as an org namespace to avoid name collisions with skills from other sources. Some skills (like `pony-ref` and `pony-ffi-audit`) are Pony-language-specific. Others (like `pony-ensemble` and `pony-code-review`) are language-agnostic methodology skills that work on any codebase — the prefix is about where they come from, not what languages they apply to.

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

```bash
python install.py --uninstall
```

This only removes the symlinks, not the cloned repo.

## Skills

### Pony Language

#### pony-ref

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

#### pony-ffi-audit

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

### Project Conventions

#### pony-examples-readme

Conventions for writing `examples/README.md` files in ponylang projects. Load it with `/pony-examples-readme` when adding, updating, or reorganizing examples.

What's in the quick reference:

- Structure conventions (title, intro paragraph, example entries, category grouping)
- Description format (what it does, what it demonstrates, key concepts)
- Ordering strategies (by complexity, by category, by directory name)
- What to omit (build instructions, source code snippets, detailed setup)

#### pony-library-readme

Conventions for writing Pony library project READMEs. Load it with `/pony-library-readme` when writing or updating a library's top-level README.

What's in the quick reference:

- Required sections in order (title, intro, status, installation, API documentation)
- Optional sections (dependencies, usage with inline code examples)
- What ponylang library READMEs deliberately omit (badges, contributing, license, table of contents)

#### pony-release-notes

How to write release notes and manage CHANGELOG entries in ponylang projects. Load it with `/pony-release-notes` when writing release notes, updating CHANGELOG, or preparing a PR with user-facing changes.

What's in the quick reference:

- Writing style (user-focused descriptions, dependency bugs as your bugs, breaking change before/after examples)
- Mechanics (`.release-notes/` directory, individual files per PR, CI aggregation)
- Changelog labels (`changelog - fixed`, `changelog - added`, `changelog - changed`)
- Single-type vs. multi-type PR workflows
- Rules for updating accumulated unreleased notes

### Development Workflow

#### pony-software-design

Disciplines for software design work — APIs, type systems, features, system boundaries. Load it with `/pony-software-design` when designing new interfaces or deciding where ownership boundaries fall. Counters the tendency to retrieve familiar patterns instead of discovering what the problem needs.

Has full (8-persona) and lightweight (5-persona) modes. Full mode runs design (3 personas) and evaluation (5 personas) stages with a feedback loop. Lightweight mode keeps all design personas but reduces evaluation to 2 personas in a single pass.

#### pony-code-review

Ensemble code review with specialized reviewer personas. Load it with `/pony-code-review` when conducting a code review of a PR, branch, or local changes.

Has full (8-persona, iterative re-review) and lightweight (3-persona, single pass) modes. Personas cover correctness, security, performance, API design, test quality, adversarial scenarios, design principles, and wildcard concerns.

#### pony-test-design

Two-stage ensemble for planning meaningful tests. Load it with `/pony-test-design` when writing tests for new features or reviewing test quality. Counters the tendency to write tests that exercise the stdlib instead of your code.

Has full (8-persona) and lightweight (5-persona) modes. Stage 1 (planning) produces a test strategy from three different analytical angles. Stage 2 (evaluation) stress-tests the strategy for coverage gaps, weak assertions, and missed property-testing opportunities.

#### pony-pbt-patterns

Property-based and generative testing patterns. Load it with `/pony-pbt-patterns` when writing property-based tests, generators, or generative test suites.

Covers the valid/invalid/mixed generator triad, compositional generator hierarchies, deriving generators from validation rules, and coverage strategies. Maps directly onto PonyCheck.

#### pony-debug

Structured debugging protocol with checkpoints. Load it with `/pony-debug` when debugging non-trivial issues — before forming any hypothesis about the cause.

Provides an OODA-loop investigation process: characterize the failure, gather context, build a minimal reproduction, then iterate through hypothesis/experiment/observe cycles until all symptoms are explained. Especially valuable for Pony's subtle failure modes (capability violations, FFI issues, actor lifecycle problems, CI timeouts from undisposed resources).

### Infrastructure

#### pony-ensemble

The mechanical process for producing higher-confidence outputs through decorrelated reasoning paths. Load it with `/pony-ensemble` when you want the ensemble approach. Multiple agents work the same problem with slightly different attention focuses, then a synthesizer integrates their outputs.

This is infrastructure — `pony-software-design`, `pony-code-review`, and `pony-test-design` all build on it with domain-specific customizations.

#### pony-synthesize

Fixed instructions for the ensemble synthesizer — integrates multiple agent outputs into a single higher-quality result. Load it with `/pony-synthesize` as part of the ensemble workflow.

This is infrastructure — loaded by `pony-ensemble` during the synthesis step.

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

### /pony-software-design

> **Load `/pony-software-design` for design work**: When the task involves designing APIs, type systems, features, or system boundaries — not just implementing an existing design — load `/pony-software-design` before starting. This includes any work where you're deciding what types to create, what a public interface looks like, or where ownership boundaries fall.

### /pony-code-review

> **Load `/pony-code-review` for code reviews**: When conducting a code review of a PR, branch, or local changes, load `/pony-code-review`. Not for one-line config changes or typo fixes.

### /pony-test-design

> **Load `/pony-test-design` when writing tests**: Before writing tests for new features or reviewing test quality, load `/pony-test-design`.

### /pony-pbt-patterns

> **Load `/pony-pbt-patterns` when writing property-based tests**: Load it when writing property-based tests, generators, or generative test suites, especially with PonyCheck.

### /pony-debug

> **Load `/pony-debug` when you start debugging**: Before forming any hypothesis about the cause of a non-trivial issue, load `/pony-debug`. It provides a structured protocol with checkpoints.
