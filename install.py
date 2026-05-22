#!/usr/bin/env python3
"""Install Pony LLM skills by symlinking skill directories into your AI harness.

Usage:
    python install.py              Install for all detected harnesses
    python install.py --claude     Install for Claude Code
    python install.py --codex      Install for Codex
    python install.py --claude --codex   Install for both
    python install.py --uninstall  Remove all symlinks pointing into this repo
    python install.py --dry-run    Show what would be done without doing it

What it does:
- Symlinks each top-level skill directory (containing SKILL.md) into the
  user-level skills directory of each selected harness:
    Claude Code: ~/.claude/skills/
    Codex:       ~/.agents/skills/

Harness selection:
- With no --claude/--codex flag, installs for every harness detected on this
  machine: Claude Code if ~/.claude exists; Codex if ~/.codex or ~/.agents
  exists. Pass --claude and/or --codex to force specific targets regardless of
  what is detected (the skills directory is created as needed).

Existing symlinks pointing into this repo are updated silently.
Existing files/directories that are NOT symlinks are never overwritten —
the script reports them and skips. Remove them manually first if you want
the symlink to take over.

On Windows, symlinks require either Developer Mode enabled or running as
administrator.
"""

import sys
from pathlib import Path

# Each harness maps to the marker directories that signal it is installed and
# the user-level skills directory (relative to home) we symlink into. Codex
# follows the cross-harness ~/.agents/skills location; ~/.codex is config-only,
# so either ~/.codex or ~/.agents counts as "Codex is present".
HARNESSES = {
    "claude": {
        "label": "Claude Code",
        "markers": (".claude",),
        "skills": (".claude", "skills"),
    },
    "codex": {
        "label": "Codex",
        "markers": (".codex", ".agents"),
        "skills": (".agents", "skills"),
    },
}


def repo_dir():
    """Return the absolute path to the repository root."""
    return Path(__file__).resolve().parent


def skills_dir(home, name):
    """Return the skills directory for a harness under the given home."""
    return home.joinpath(*HARNESSES[name]["skills"])


def detected(home, name):
    """Return True if the harness appears installed (a marker dir exists)."""
    return any((home / marker).is_dir() for marker in HARNESSES[name]["markers"])


def selected_harnesses(args, home):
    """Resolve which harnesses to act on: forced by flags, else detected."""
    forced = [name for name in HARNESSES if f"--{name}" in args]
    if forced:
        return forced
    return [name for name in HARNESSES if detected(home, name)]


def blocking_ancestor(path):
    """Return the nearest existing ancestor of path that is not a directory.

    Detects when a skills directory cannot be created because a parent
    component is a file or a broken symlink. Returns None when the path is
    creatable (its nearest existing ancestor is a directory).
    """
    for candidate in (path, *path.parents):
        if candidate.is_symlink() and not candidate.exists():
            return candidate
        if candidate.exists():
            return None if candidate.is_dir() else candidate
    return None


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


def install_into(repo, skills_dst, dry_run):
    """Symlink each skill directory (top-level dirs with SKILL.md) into skills_dst."""
    blocker = blocking_ancestor(skills_dst)
    if blocker is not None:
        print(f"  SKIP (not a directory): {blocker}")
        return
    found_any = False
    for skill_dir in sorted(repo.iterdir()):
        if not skill_dir.is_dir():
            continue
        if not (skill_dir / "SKILL.md").exists():
            continue
        found_any = True
        print(symlink(skill_dir, skills_dst / skill_dir.name, dry_run))
    if not found_any:
        print("  (no skill directories found)")
    remove_stale_symlinks(repo, skills_dst, dry_run)


def remove_stale_symlinks(repo, skills_dst, dry_run):
    """Remove symlinks in skills_dst that point into repo but whose targets are gone."""
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
        print("  Stale skill symlinks:")
        for entry in stale:
            if not dry_run:
                entry.unlink()
            print(f"    remove: {entry}")


def uninstall(repo, skills_dst, dry_run):
    """Remove all symlinks in skills_dst that point into repo."""
    if not skills_dst.is_dir():
        print("  Nothing to uninstall (skills directory does not exist).")
        return
    removed = []
    for entry in sorted(skills_dst.iterdir()):
        if not entry.is_symlink():
            continue
        target = entry.resolve()
        try:
            target.relative_to(repo.resolve())
        except ValueError:
            continue
        removed.append(entry)
    if not removed:
        print("  No symlinks pointing into this repo found.")
        return
    print("  Removing:")
    for entry in removed:
        if not dry_run:
            entry.unlink()
        print(f"    {entry}")


def main():
    """Install or uninstall skills for the selected/detected harnesses."""
    args = sys.argv[1:]
    if "-h" in args or "--help" in args:
        print(__doc__.strip())
        sys.exit(0)

    known = {"--dry-run", "--uninstall", "--claude", "--codex"}
    unknown = [arg for arg in args if arg not in known]
    if unknown:
        print(f"Unknown option(s): {' '.join(unknown)}")
        print("Run with --help for usage.")
        sys.exit(2)

    dry_run = "--dry-run" in args
    do_uninstall = "--uninstall" in args

    if dry_run:
        print("=== DRY RUN (no changes will be made) ===\n")

    repo = repo_dir()
    home = Path.home()
    targets = selected_harnesses(args, home)

    if not targets:
        print("No supported harness detected (looked for ~/.claude, ~/.codex, "
              "~/.agents).")
        if do_uninstall:
            print("Pass --claude and/or --codex to uninstall from a specific "
                  "harness.")
        else:
            print("Pass --claude and/or --codex to install anyway.")
        return

    for name in targets:
        dst = skills_dir(home, name)
        print(f"{HARNESSES[name]['label']} ({dst}):")
        if do_uninstall:
            uninstall(repo, dst, dry_run)
        else:
            install_into(repo, dst, dry_run)
        print()

    if dry_run:
        print("=== DRY RUN complete (no changes were made) ===")
    else:
        print("Done.")


if __name__ == "__main__":
    main()
