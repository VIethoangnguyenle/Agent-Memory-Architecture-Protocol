#!/usr/bin/env bash
# AMAP installer — bootstrap a venv and scaffold/update AMAP into a target project.
#
# Usage: ./install.sh /path/to/your/project
set -euo pipefail

AMAP_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$AMAP_ROOT/.venv"

TARGET="${1:-}"
if [ -z "$TARGET" ]; then
  echo "Usage: ./install.sh /path/to/your/project"
  exit 1
fi
if [ ! -d "$TARGET" ]; then
  echo "❌ Target directory does not exist: $TARGET"
  exit 1
fi
TARGET="$(cd "$TARGET" && pwd)"

# Require python3 >= 3.8.
if ! command -v python3 >/dev/null 2>&1; then
  echo "❌ python3 not found. Please install Python 3.8 or newer."
  exit 1
fi

# Create the venv on first run and install dependencies.
if [ ! -d "$VENV" ]; then
  echo "→ Creating virtualenv at $VENV"
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install --quiet --upgrade pip
  "$VENV/bin/pip" install --quiet "jinja2>=3.1" "pyyaml>=6.0"
fi

PY="$VENV/bin/python"

# Route to update if AMAP already installed, else init.
if [ -f "$TARGET/.agent/resolved-config.yaml" ]; then
  echo "→ Existing AMAP install detected — updating."
  ( cd "$AMAP_ROOT" && "$PY" -m cli.amap update --target "$TARGET" )
else
  echo "→ Fresh install."
  ( cd "$AMAP_ROOT" && "$PY" -m cli.amap init --target "$TARGET" )
fi
