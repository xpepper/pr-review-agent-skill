from pathlib import Path

import pytest

from check_skills import check_skill

VALID_FRONTMATTER = """---
name: {name}
description: {description}
license: MIT
compatibility: Requires gh CLI.
metadata:
  author: Someone
  version: "1.0.0"
allowed-tools: Bash
---
"""


def make_skill(root: Path, name="my-skill", description="Use when testing.", body="", frontmatter=None):
    skill_dir = root / name
    skill_dir.mkdir()
    text = frontmatter if frontmatter is not None else VALID_FRONTMATTER.format(name=name, description=description)
    (skill_dir / "SKILL.md").write_text(text + body)
    return skill_dir


def test_valid_skill_has_no_errors(tmp_path):
    assert check_skill(make_skill(tmp_path)) == []


def test_name_must_match_directory(tmp_path):
    skill_dir = make_skill(tmp_path, frontmatter=VALID_FRONTMATTER.format(name="other", description="Use when x."))
    assert any("does not match directory" in e for e in check_skill(skill_dir))


@pytest.mark.parametrize("field", ["description", "license", "compatibility", "allowed-tools"])
def test_required_top_level_field_missing(tmp_path, field):
    lines = [l for l in VALID_FRONTMATTER.format(name="my-skill", description="Use when x.").splitlines()
             if not l.startswith(f"{field}:")]
    skill_dir = make_skill(tmp_path, frontmatter="\n".join(lines) + "\n")
    assert any(f"missing '{field}'" in e for e in check_skill(skill_dir))


@pytest.mark.parametrize("field", ["author", "version"])
def test_required_metadata_field_missing(tmp_path, field):
    lines = [l for l in VALID_FRONTMATTER.format(name="my-skill", description="Use when x.").splitlines()
             if not l.strip().startswith(f"{field}:")]
    skill_dir = make_skill(tmp_path, frontmatter="\n".join(lines) + "\n")
    assert any(f"missing 'metadata.{field}'" in e for e in check_skill(skill_dir))


def test_description_must_start_with_use_when(tmp_path):
    skill_dir = make_skill(tmp_path, description="Reviews PRs.")
    assert any("Use when" in e for e in check_skill(skill_dir))


def test_description_may_start_with_use_only_when(tmp_path):
    assert check_skill(make_skill(tmp_path, description="Use only when invoked.")) == []


def test_missing_frontmatter(tmp_path):
    skill_dir = make_skill(tmp_path, frontmatter="# No frontmatter\n")
    assert any("frontmatter" in e for e in check_skill(skill_dir))


def test_invalid_yaml(tmp_path):
    skill_dir = make_skill(tmp_path, frontmatter="---\nname: [unclosed\n---\n")
    assert any("YAML" in e for e in check_skill(skill_dir))


def test_referenced_file_must_exist(tmp_path):
    skill_dir = make_skill(tmp_path, body="Read `references/guide.md` first.\n")
    assert any("references/guide.md" in e for e in check_skill(skill_dir))


def test_existing_referenced_file_passes(tmp_path):
    skill_dir = make_skill(tmp_path, body="Read `references/guide.md` first.\n")
    (skill_dir / "references").mkdir()
    (skill_dir / "references" / "guide.md").write_text("guide")
    assert check_skill(skill_dir) == []
