#!/bin/sh
# Install the AMAP mechanical-enforcement pre-commit hook into a target Java project.
# Usage: install.sh <project_root> <dna_path> <conv_path>
set -e
PROJECT_ROOT="${1:?usage: install.sh <project_root> <dna_path> <conv_path>}"
DNA_PATH="${2:?dna_path required}"
CONV_PATH="${3:?conv_path required}"
HERE=$(cd "$(dirname "$0")" && pwd)
RULESET_PATH="$PROJECT_ROOT/.amap/tools/rule-projector/generated/checkstyle.generated.xml"

# 1. Generate ruleset
python3 "$HERE/projector.py" --dna "$DNA_PATH" --conventions "$CONV_PATH" --out "$PROJECT_ROOT/.amap/tools/rule-projector/generated"
python3 "$HERE/backends/checkstyle.py" --ir "$PROJECT_ROOT/.amap/tools/rule-projector/generated/rules.json" --out "$RULESET_PATH"

# 2. Install hook with config baked in
HOOK="$PROJECT_ROOT/.git/hooks/pre-commit"
{
  echo "#!/bin/sh"
  echo "export DNA_PATH='$DNA_PATH'"
  echo "export CONV_PATH='$CONV_PATH'"
  echo "export RULESET_PATH='$RULESET_PATH'"
  echo "exec sh '$HERE/hooks/pre-commit.sh'"
} > "$HOOK"
chmod +x "$HOOK"
echo "Installed pre-commit hook -> $HOOK"
