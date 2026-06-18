#!/bin/sh
# AMAP rule-projector pre-commit gate. Installed by install.sh into target Java project.
# Config via env (set by install.sh): DNA_PATH, CONV_PATH, RULESET_PATH
set -e
: "${DNA_PATH:?DNA_PATH not set}"
: "${CONV_PATH:?CONV_PATH not set}"
: "${RULESET_PATH:?RULESET_PATH not set}"

# 1. Sync-check
CUR=$(cat "$DNA_PATH" "$CONV_PATH" | sha256sum | cut -d' ' -f1)
EMB=$(grep -o 'source_hash=[a-f0-9]*' "$RULESET_PATH" | head -1 | cut -d= -f2)
if [ "$CUR" != "$EMB" ]; then
  echo "⛔ DNA/conventions changed but ruleset is stale."
  echo "   Run: python3 {{ platform.framework_root }}/tools/rule-projector/projector.py --dna \"$DNA_PATH\" --conventions \"$CONV_PATH\" --out generated/"
  echo "   then regenerate checkstyle and commit the ruleset."
  exit 1
fi

# 2. Checkstyle on staged Java files
FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.java$' || true)
if [ -n "$FILES" ]; then
  if ! command -v checkstyle >/dev/null 2>&1; then
    echo "⚠ checkstyle CLI not found — skipping mechanical lint (install checkstyle to enforce)."
    exit 0
  fi
  checkstyle -c "$RULESET_PATH" $FILES
fi
exit 0
