# Documentation Principles

These are the principles this review audits documentation against — a project-agnostic baseline. If the project under review has its own `AGENTS.md`, style guide, or documentation conventions, audit against those as well; they are usually more specific and take precedence where they conflict with this baseline.

## Principles

- **Prefer explicit over implicit**: State things directly rather than relying on the reader to reconstruct implicit or assumed knowledge. A few extra words cost less than a reader rebuilding hidden context.

- **Handle sensitive data deliberately**: Documentation must not expose secrets, credentials, internal hostnames, or other sensitive data. Flag anything that should be redacted or doesn't belong in published docs.

- **Document coupling at the point of breakage**: When something depends on another component's internal behavior (a read sequence, execution order, a size assumption), document that dependency where a future maintainer would break it — not only where it's consumed.

- **Document every type parameter**: Reference documentation for a generic type should explain what each type parameter carries — including ones that appear only in field types and look "phantom." They still carry information, and they are exactly the ones that get left undocumented.

- **Documented behavior is a commitment**: A documented guarantee is a contract — easier to add than to retract, because readers come to depend on it. Don't over-promise; document what will actually be held to.

- **Don't paper over a confusing design with caveats**: If a passage needs piling on qualifications and special-case caveats to make sense, the underlying design — or the document's organization — is the real problem. Flag that rather than burying it in more prose.

- **Probe external behavior empirically**: Documentation describing an external API, file format, protocol, or data source should reflect what was actually verified against the real thing — not reproduced secondhand from other documentation, or assumed from reasoning. Unverified external claims are where docs go quietly wrong.

- **Evaluate copied patterns, don't cargo-cult them**: When reusing a document structure or template, copy the intent, not the incidental choices. Strip it to what this document actually needs, then add back only what's justified.

- **Don't hard-wrap prose**: Markdown should flow naturally and break only on paragraph boundaries; don't insert line breaks mid-paragraph to keep lines short. Let the renderer wrap to the container width.

- **Consistency across repetitive structure**: When documentation repeats a structure across sections or entries (API entries, tutorial steps, example descriptions), hold the same format and rigor across all of them. The last entry deserves the same care as the first; inconsistency is a smell.

- **Document public API elements**: Public-facing API elements should be documented. Missing documentation for a public element is a principle violation, not merely a coverage gap.

- **Fix what your change makes stale**: When a change invalidates something elsewhere — a cross-reference, an index entry, navigation, a code example, a screenshot — fix it in the same change. "I didn't touch that line" isn't an excuse when your change is what made it wrong.

- **Bulk find-replace is risky**: A global rename of a term across documentation can clobber substrings of larger words (rename "Reader" and you also hit "ReaderWriter"). Verify substring safety — use a contextual pattern — before running a global replace.

- **Package docstrings should guide, not just describe**: A package- or module-level docstring is the reader's entry point. It should steer readers toward the right API choices, not just enumerate what exists — especially when multiple APIs serve overlapping purposes and some are safer for common cases. Say so, with reasoning.
