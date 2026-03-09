#!/bin/bash
set -euo pipefail

SKILL_DIR="${HOME}/.claude/skills"
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

mkdir -p "$SKILL_DIR"

for dir in "$REPO_DIR"/*/; do
  [ -f "$dir/SKILL.md" ] || continue
  skill=$(basename "$dir")
  ln -sfn "$dir" "$SKILL_DIR/$skill"
  echo "Installed $skill"
done
