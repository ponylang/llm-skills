# Pony LLM Skills — project instructions

Instructions for working in this repository.

<!-- contributor-only -->
## Contributing

Before contributing to this repository, read [CONTRIBUTING.md](CONTRIBUTING.md).
<!-- /contributor-only -->

## Pull requests

**On a changelog-labeled PR, write the description like a release note.** A PR carrying a `changelog - *` label documents a user-facing change, and the generated CHANGELOG entry links readers straight to the PR — so the PR description is what a reader lands on. Write it for the person *using* the skills, not for someone reading the implementation: plain language, the user-visible impact, and why it matters — not an enumeration of the internal mechanics. Keep it short. (Example — PR #36's description read: The code review skill was pointing at my personal CLAUDE.md to get information which made it perform "subpar" when others used it.)

## Harness-specific content

**Don't include anything specific to a particular harness without express approval from the user.** The skills in this repository are meant to work across coding harnesses, not just one, so Claude-only or Codex-only instructions, paths, or command syntax don't belong here by default. When a change does include harness-specific content, call it out explicitly in the pull request.
