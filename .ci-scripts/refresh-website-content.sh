#!/bin/bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
REF_DIR="$REPO_DIR/pony-ref/references"

echo "Fetching website content..."

curl -sfL https://tutorial.ponylang.io/llms.txt -o "$REF_DIR/tutorial-llms.txt"
curl -sfL https://tutorial.ponylang.io/llms-full.txt -o "$REF_DIR/tutorial-llms-full.txt"
curl -sfL https://patterns.ponylang.io/llms.txt -o "$REF_DIR/patterns-llms.txt"
curl -sfL https://patterns.ponylang.io/llms-full.txt -o "$REF_DIR/patterns-llms-full.txt"
curl -sfL https://www.ponylang.io/llms.txt -o "$REF_DIR/website-llms.txt"
curl -sfL https://www.ponylang.io/llms-full.txt -o "$REF_DIR/website-llms-full.txt"

echo "Done."
