#!/usr/bin/env bash
# Safe cleanup of ignored files but preserve .aider* files
# Usage: ./scripts/clean_ignored.sh

set -euo pipefail

echo "Cleaning ignored files but excluding .aider* and .aider.tags.cache.v4..."
# -f : force
# -d : remove untracked directories
# -X : remove only ignored files
# -e : pattern to exclude from removal
git clean -f -d -X -e .aider* -e .aider.tags.cache.v4

echo "Done."
