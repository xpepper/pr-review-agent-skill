# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""Check every skill's SKILL.md against the mechanical rules in AGENTS.md.

Usage: uv run scripts/check_skills.py [repo-root]
"""

import re
import sys
from pathlib import Path

import yaml

REQUIRED_FIELDS = ["description", "license", "compatibility", "allowed-tools"]
REQUIRED_METADATA = ["author", "version"]
# "Use only when" is accepted for manual-only skills (see guided-flow-review).
DESCRIPTION_PREFIXES = ("Use when", "Use only when")
REFERENCE_PATTERN = re.compile(r"references/[A-Za-z0-9._/-]+\.md")


def check_skill(skill_dir: Path) -> list[str]:
    text = (skill_dir / "SKILL.md").read_text()
    match = re.match(r"---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        return ["no YAML frontmatter delimited by '---' at the top of the file"]
    try:
        frontmatter = yaml.safe_load(match.group(1))
    except yaml.YAMLError as error:
        return [f"invalid YAML frontmatter: {error}"]
    if not isinstance(frontmatter, dict):
        return ["frontmatter is not a YAML mapping"]

    errors = []
    if frontmatter.get("name") != skill_dir.name:
        errors.append(f"name '{frontmatter.get('name')}' does not match directory '{skill_dir.name}'")
    errors += [f"missing '{field}'" for field in REQUIRED_FIELDS if not frontmatter.get(field)]
    metadata = frontmatter.get("metadata") or {}
    errors += [f"missing 'metadata.{field}'" for field in REQUIRED_METADATA if not metadata.get(field)]

    description = frontmatter.get("description")
    if isinstance(description, str) and not description.startswith(DESCRIPTION_PREFIXES):
        errors.append("description must start with 'Use when' (or 'Use only when')")

    for reference in sorted(set(REFERENCE_PATTERN.findall(text))):
        if not (skill_dir / reference).is_file():
            errors.append(f"referenced file '{reference}' does not exist")
    return errors


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    skill_dirs = sorted(p.parent for p in root.glob("*/SKILL.md"))
    if not skill_dirs:
        print(f"No skills found under {root.resolve()}")
        return 1
    failed = False
    for skill_dir in skill_dirs:
        errors = check_skill(skill_dir)
        print(f"{'FAIL' if errors else 'ok  '} {skill_dir.name}")
        for error in errors:
            print(f"     - {error}")
        failed = failed or bool(errors)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
