#!/usr/bin/env python3
"""Install Pony LLM skills by symlinking skill directories into Claude Code.

Usage:
    python install.py              Install (create symlinks)
    python install.py --dry-run    Show what would be done without doing it

What it does:
- Symlinks each top-level skill directory (containing SKILL.md) into
  ~/.claude/skills/

Existing symlinks pointing into this repo are updated silently.
Existing files/directories that are NOT symlinks are never overwritten —
the script reports them and skips. Remove them manually first if you want
the symlink to take over.

On Windows, symlinks require either Developer Mode enabled or running as
administrator.
"""

import sys
from pathlib import Path


def repo_dir():
    """Return the absolute path to the repository root."""
    return Path(__file__).resolve().parent


def claude_home():
    """Return the path to ~/.claude."""
    return Path.home() / ".claude"


def symlink(src, dst, dry_run):
    """Create a symlink from dst -> src. Returns a status message."""
    if dst.is_symlink():
        current_target = dst.resolve()
        if current_target == src.resolve():
            return f"  skip (already linked): {dst}"
        if not dry_run:
            dst.unlink()
            dst.symlink_to(src, target_is_directory=src.is_dir())
        return f"  update link: {dst} -> {src}"

    if dst.exists():
        return f"  SKIP (exists, not a symlink): {dst}"

    if not dry_run:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.symlink_to(src, target_is_directory=src.is_dir())
    return f"  link: {dst} -> {src}"


def remove_stale_symlinks(repo, skills_dst, dry_run):
    """Remove symlinks in skills_dst that point into repo but whose targets no longer exist."""
    if not skills_dst.is_dir():
        return
    stale = []
    for entry in sorted(skills_dst.iterdir()):
        if not entry.is_symlink():
            continue
        target = entry.resolve()
        try:
            target.relative_to(repo.resolve())
        except ValueError:
            continue
        if not target.exists():
            stale.append(entry)
    if stale:
        print("\nStale skill symlinks:")
        for entry in stale:
            if not dry_run:
                entry.unlink()
            print(f"  remove: {entry}")


def main():
    """Install skills by symlinking into ~/.claude/skills/."""
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print(__doc__.strip())
        sys.exit(0)

    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("=== DRY RUN (no changes will be made) ===\n")

    repo = repo_dir()
    home = claude_home()

    # Symlink each skill directory (top-level dirs containing SKILL.md)
    print("Skills:")
    found_any = False
    for skill_dir in sorted(repo.iterdir()):
        if not skill_dir.is_dir():
            continue
        if not (skill_dir / "SKILL.md").exists():
            continue
        found_any = True
        dst = home / "skills" / skill_dir.name
        print(symlink(skill_dir, dst, dry_run))

    if not found_any:
        print("  (no skill directories found)")

    remove_stale_symlinks(repo, home / "skills", dry_run)

    if dry_run:
        print("\n=== DRY RUN complete (no changes were made) ===")
    else:
        print("\nDone.")


if __name__ == "__main__":
    main()
