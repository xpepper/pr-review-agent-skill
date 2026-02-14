#!/bin/bash
# Package agent skills into .skill files.
# Discovers all skill directories that contain a SKILL.md automatically.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PACKAGED=0

for SKILL_DIR in */; do
  SKILL="${SKILL_DIR%/}"

  [ ! -f "${SKILL}/SKILL.md" ] && continue

  SKILL_FILE="${SKILL}.skill"

  echo "Packaging ${SKILL}..."
  cd "${SKILL}"
  zip -r "../${SKILL_FILE}" . -x "*.DS_Store" -x "__pycache__/*" -x "*.pyc"
  cd ..

  SIZE=$(ls -lh "${SKILL_FILE}" | awk '{print $5}')
  echo "✓ Created: ${SKILL_FILE} ($SIZE)"
  PACKAGED=$((PACKAGED + 1))
done

if [ "$PACKAGED" -eq 0 ]; then
  echo "No skills found (no directory with SKILL.md)."
  exit 1
fi

echo ""
echo "Packaged ${PACKAGED} skill(s)."
