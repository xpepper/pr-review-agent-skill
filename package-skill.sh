#!/bin/bash
# Package agent skills into .skill files

set -e

SKILLS=("pr-review-loop")

for SKILL in "${SKILLS[@]}"; do
  SKILL_FILE="${SKILL}.skill"

  if [ ! -d "$SKILL" ]; then
    echo "Error: Skill directory '$SKILL' not found"
    exit 1
  fi

  if [ ! -f "$SKILL/SKILL.md" ]; then
    echo "Error: SKILL.md not found in '$SKILL'"
    exit 1
  fi

  echo "Packaging $SKILL..."
  cd "$SKILL"
  zip -r "../${SKILL_FILE}" . -x "*.DS_Store" -x "__pycache__/*" -x "*.pyc"
  cd ..

  SIZE=$(ls -lh "${SKILL_FILE}" | awk '{print $5}')
  echo "✓ Created: ${SKILL_FILE} ($SIZE)"
done
