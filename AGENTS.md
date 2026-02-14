# Agent Development Guide

This document describes conventions for AI agents working on this repository.

## What this repo is

A collection of [Agent Skills](https://agentskills.io) for automating PR code review workflows. Each skill lives in its own directory and is packaged into a `.skill` file for distribution.

## Repo structure

```
<skill-name>/           # one directory per skill
  SKILL.md              # skill definition (required)
  README.md             # user-facing documentation (recommended)
  references/           # supporting reference documents (optional)
<skill-name>.skill      # packaged skill — build artifact, gitignored
docs/plans/             # implementation plans
package-skill.sh        # packaging script
```

## SKILL.md conventions

Every `SKILL.md` must have YAML frontmatter at the top:

```yaml
---
name: skill-name-with-hyphens
description: Use when <triggering conditions>. <Key capabilities>. <Any important limitations>.
license: MIT
compatibility: <what the agent needs installed to use this skill>
metadata:
  author: Pietro Di Bello
  version: "1.0.0"
allowed-tools: Bash(gh:*)
---
```

Rules:
- `name`: letters, numbers, and hyphens only — must match the directory name
- `description`: starts with "Use when", written in third person, describes triggering conditions and key capabilities (not the internal workflow)
- `allowed-tools`: list only tools the skill actually needs (e.g. `Bash(gh:*)` for skills that call the `gh` CLI)
- `version`: bump when making breaking changes to the skill's behaviour

## Adding a new skill

1. Create `<skill-name>/SKILL.md` with the frontmatter above
2. Add `<skill-name>/README.md` with install instructions and a description of what the skill does
3. Add any reference documents under `<skill-name>/references/`
4. Run `./package-skill.sh` to build the `.skill` package
5. Push, then verify with the test cycle below

## Packaging

```bash
./package-skill.sh
```

Auto-discovers all directories containing a `SKILL.md`. Generated `.skill` files are gitignored.

## Testing a skill

After pushing changes, verify install and removal work:

```bash
# Install
npx skills add xpepper/pr-review-agent-skill/<skill-name> -a claude-code --yes

# Check: the skill description should appear, install path should be .agents/skills/<skill-name>
# Then remove
npx skills remove <skill-name> -a claude-code --yes
```

Without `--global`, skills install project-locally into `.agents/skills/` (gitignored). Use `--global` to install into the agent's global skills directory.

## Commit conventions

Follow [Conventional Commits](https://www.conventionalcommits.org/):
- `feat(<skill>):` — new skill or new capability in an existing skill
- `fix(<skill>):` — correction to skill content or behaviour
- `docs(<skill>):` — README or reference document changes
- `build:` — changes to `package-skill.sh` or repo tooling
- `chore:` — gitignore, project config, maintenance

Subject line: imperative mood, lowercase, no period, max 72 chars.
