#!/usr/bin/env bash
# Safe cleanup of ignored files but preserve .aider* files
# Usage: ./scripts/clean_ignored.sh

set -euo pipefail

echo "Cleaning ignored files but excluding '.aider*' and '.aider.tags.cache.v4'..."
# Approach:
# 1. Run `git clean -n -X -d` to list ignored files (lines like: "Would remove <path>")
# 2. Extract paths, exclude those matching the .aider* patterns, and remove the rest with rm -rf.
# This avoids relying on git's -e exclusion which may behave inconsistently across versions.

# Get raw list of ignored paths (one per line)
ignored_paths=$(git clean -n -X -d | sed -n "s/^Would remove //p")

if [ -z "$ignored_paths" ]; then
	echo "No ignored files to remove."
	exit 0
fi

# Filter out .aider* and .aider.tags.cache.v4
to_remove=$(printf "%s\n" "$ignored_paths" | grep -vE "^\.aider" | grep -v "^.aider.tags.cache.v4$" || true)

if [ -z "$to_remove" ]; then
	echo "No files to remove after excluding .aider* patterns."
	exit 0
fi

echo "The following ignored files/directories will be removed:" 
printf "%s\n" "$to_remove"

# Remove safely, handling spaces and special characters. Use null-delimited xargs.
printf "%s\0" "$to_remove" | xargs -0 rm -rf --

echo "Removed listed ignored files (excluded .aider* patterns)."

echo "Done."
