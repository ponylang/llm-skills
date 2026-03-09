# Pony LLM Skills

Skills for working with [Pony](https://www.ponylang.io) in [Claude Code](https://docs.anthropic.com/en/docs/claude-code). Each skill is a self-contained reference that Claude loads on demand during coding sessions.

## Installation

Clone the repo and run the install script. It symlinks each skill into your Claude Code skills directory so they stay up to date when you pull.

```bash
git clone https://github.com/ponylang/llm-skills.git
cd llm-skills
./install.sh
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
rm ~/.claude/skills/pony-ref
# repeat for any other installed skills
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
