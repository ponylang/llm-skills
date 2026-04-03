---
name: pony-release-notes
description: Load when writing release notes, updating CHANGELOG, or preparing a PR that includes user-facing changes in a Pony project.
disable-model-invocation: false
---

# Pony Release Notes & CHANGELOG

## Writing Style

**Release notes — write for end users, not developers**: Release notes describe user-visible changes only. Omit implementation details (internal refactoring, which functions changed, how the fix works). Focus on what the user experienced before, what they experience now, and why it matters. When introducing new API surface, include a short code example — a concise usage snippet communicates more than descriptive text. Changes that are only relevant to maintainers (internal documentation, code comments, refactoring with no user-visible effect) don't get release notes at all.

**Dependency bugs are your bugs**: When a dependency upgrade fixes a bug, write the release note as if it's your bug. The user doesn't care which layer caused it — they care that the library they use had a problem and now it doesn't. Don't mention the dependency name, don't say "upgrades X to Y," don't write "the underlying Z library." Just describe the problem and that it's fixed.

**Dependency upgrades can produce multiple change types**: A single dependency upgrade might bring new features (added), bug fixes (fixed), and breaking changes (changed). Evaluate each user-visible consequence independently rather than treating the upgrade as one item. A dependency bump that fixes two bugs and adds a feature is three release note entries, not one.

**Breaking changes need before/after examples**: When a release note describes a breaking change, include before/after code snippets showing what users need to change. This lets users quickly see the migration path without reading the full description.

**Code examples should show contrast, not compressed workflows**: When a documentation example's purpose is "here's an alternative way to do X," show the two approaches to the same operation side by side. Don't try to compress a full end-to-end workflow into a tiny snippet with `// ...` placeholders — it loses clarity. This applies to READMEs, release notes, and docstrings.

**One paragraph per line**: Each prose paragraph in a release note should be a single line (no hard wraps). Code blocks are exempt — they follow their natural formatting. This matches how the CI tooling aggregates release notes.

## Mechanics

**How to add release notes in Pony projects**: Create a `.md` file in the `.release-notes/` directory with any unique, descriptive name (e.g., `remove-command.md`). Format: `## Title` followed by an end-user description. Do NOT edit `next-release.md` directly — CI aggregates the individual files into that on release. The file can be included in the PR that introduces the change.

**Three types of user-facing changes**: Fixed (bug fixes), Added (new features), Changed (breaking changes or conceptual changes). Most PRs are a single type, which the automation handles — do NOT include a manual CHANGELOG step in plans for single-type PRs. After opening the PR, apply the corresponding label so CI knows which CHANGELOG section to use: `changelog - fixed`, `changelog - added`, or `changelog - changed`. When a PR spans multiple types (e.g., both Added and Changed), the automation can't handle it — you must manually:
1. Open the PR first to get a PR number.
2. Update `CHANGELOG.md` directly, adding a line to each relevant section under `[unreleased]`. Each line should be the best short description for that specific change (not necessarily the PR title), formatted as `- Description ([PR #N](url))`. A single PR can have multiple entries in the same section (e.g., multiple Changed lines) if there are multiple distinct breaking changes.
3. Append the release notes directly to `.release-notes/next-release.md` — one `## Title` section per change type.
4. Do NOT create an individual `.release-notes/*.md` file for multi-type PRs.
5. Do NOT apply a `changelog` label — labels and manual CHANGELOG/next-release.md edits are mutually exclusive.

**PR title must match release note title for single-type PRs**: When using a changelog label, the automation uses the PR title as the CHANGELOG entry. The release note heading (the `## Title` line) and the PR title must be the same text, so users see a consistent name in the CHANGELOG and the release notes.

**Breaking changes must update existing unreleased notes**: When a breaking change modifies API that an earlier unreleased PR introduced, check `next-release.md` for code examples or descriptions that reference the old API. Accumulated unreleased notes go stale when a later PR breaks something an earlier one added.

**Omit never-released features entirely**: If a feature was introduced and removed between releases (never shipped to users), it should not appear in release notes or CHANGELOG at all. Users never saw it, so documenting its addition or removal is meaningless. Describe the net change from the last release to the current state.

**Only make factual changes to existing entries**: When updating accumulated unreleased notes, only change content that is factually wrong (stale API references, incorrect descriptions). Do not make grammar, formatting, or stylistic edits to entries from earlier PRs.
