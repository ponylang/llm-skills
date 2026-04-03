---
name: pony-examples-readme
description: Conventions for Pony examples/README.md files. Load when adding, updating, or reorganizing examples in a ponylang project.
disable-model-invocation: false
---

# Pony Examples README Conventions

These conventions are derived from existing ponylang examples/README.md files (postgres, redis, lori, crdt, uri, web_link). Follow them when writing or updating an examples/README.md.

## Structure

1. **Title** — Always `# Examples`.

2. **Intro paragraph** (no heading) — 1-3 sentences describing what the examples are and any useful context. Standard phrasing for library examples: "Each subdirectory is a self-contained Pony program demonstrating a different part of the X library." If examples are ordered by complexity or grouped by category, state that here.

3. **Example entries** — One `##` heading per example, using the directory name as the heading text. Optionally link to the directory: `## [example-name](example-name/)`.

4. **Category grouping** (when applicable) — If examples fall into natural categories, use `##` for category headings and `###` for individual examples within each category.

5. **Start-here marker** — When one example is clearly the simplest entry point, end its description with: "Start here if you're new to the library."

## Example Descriptions

Each example gets a paragraph of 2-4 sentences covering:

- **What it does**: The concrete workflow in present tense, third person ("Connects to Redis, executes SET, prints the response, and closes the session.")
- **What it demonstrates**: The specific APIs, interfaces, or patterns exercised, named with backtick formatting (e.g., "`Session.prepare()` and `NamedPreparedQuery`")
- **Key concepts**: Any non-obvious behavior, design pattern, or protocol detail the example illustrates

## Ordering

Choose one strategy and make it clear from the intro paragraph or the order itself:

- **By complexity** (simplest first) — Best when examples build on each other conceptually. State the ordering in the intro: "Ordered from simplest to most involved."
- **By category** — Best when examples cover distinct feature areas. Use `##` categories with `###` examples.
- **By directory name** — Acceptable when no natural ordering exists.

## What to Omit

- **Build instructions** — Build commands belong in the project's top-level README or Makefile. Exception: if examples have a separate build target (e.g., `make build-examples`), a one-line note in the intro is acceptable.
- **Source code snippets** — The README describes what each example does; the code speaks for itself.
- **Detailed setup instructions** — If an example needs external services (a database, Redis server, TLS certificates), mention it briefly in that example's description. Detailed setup belongs in the example's own directory.
