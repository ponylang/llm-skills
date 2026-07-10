---
name: pony-library-readme
description: Conventions for Pony library project READMEs. Load when writing or updating a README.md for a ponylang library project.
disable-model-invocation: false
---

# Pony Library README Conventions

These conventions are derived from existing ponylang library READMEs and should be followed when writing or updating a README.md for a Pony library project.

Load `pony-prose` for how the prose reads. This skill says what a README holds; `pony-prose` says how to write it plainly.

## Required Sections (in order)

Every Pony library README has these sections in this order:

1. **Title** (`#`) — Lowercase matching the repo/package name (e.g., `# glob`, `# web_link`). Use proper capitalization only for proper nouns or acronyms (e.g., `# PEG`, `# Lori`, `# GitHub REST API`).

2. **Intro paragraph** (no heading) — 1-2 sentences describing what the library does. No section heading.

3. **`## Status`** — Short maturity statement. Common values:
   - `Production ready.`
   - `Beta`
   - `[Name] is beta-level software.`
   - Longer form: `[Name] is beta quality software that will change frequently. Expect breaking changes. That said, you should feel comfortable using it in your projects.`

4. **`## Installation`** — Standard 5-bullet list using `*` markers:
   ```markdown
   * Install [corral](https://github.com/ponylang/corral)
   * `corral add github.com/ponylang/<name>.git --version <X.Y.Z>`
   * `corral fetch` to fetch your dependencies
   * `use "<package>"` to include this package
   * `corral run -- ponyc` to compile your application
   ```
   If the package has sub-packages, the `use` bullet gets sub-bullets listing each (e.g., `use "ssl/crypto"`, `use "ssl/net"`).

5. **`## API Documentation`** — A markdown link to the docs: `[https://ponylang.github.io/<name>](https://ponylang.github.io/<name>)`. This is always the last section (or near-last if a project-specific section follows).

## Optional Sections

These go between Installation and API Documentation, in this order:

- **`## Dependencies`** — Only include when the library requires native C libraries the user must install (e.g., libpcre2, OpenSSL). If the dependency is transitive via the `ssl` package, a note after the installation bullets linking to ssl's installation instructions is sufficient instead of a full section.

- **`## Usage`** — Always include an inline code example showing core usage (a complete short program or a structural skeleton). Point to the `examples/` directory for more.

## Things Pony Library READMEs Do NOT Have

- No CI/coverage/version badges
- No "Contributing" section (that goes in CONTRIBUTING.md)
- No "License" section (that goes in LICENSE)
- No "Table of Contents"
