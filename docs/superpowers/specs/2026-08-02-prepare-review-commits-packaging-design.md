# Prepare Review Commits Packaging Design

## Decision

Add `prepare-review-commits` to this repository as a first-class Agent Skill.
Do not create a separate repository or a mirror.

## Repository role

This repository covers the PR preparation and review lifecycle:

1. `prepare-review-commits` organizes uncommitted changes into a review-ready
   sequence before a branch is pushed.
2. The existing review-loop skills handle feedback after a pull request exists.

The root README must be repositioned from PR code review workflows to PR
preparation and review workflows, and list the preparation skill before review
skills.

## Distribution

The new skill remains a sibling directory under the repository root and follows
the existing package layout:

```text
prepare-review-commits/
  SKILL.md
  README.md
```

The existing `package-skill.sh` discovers and packages it automatically. Users
install it through the same catalog:

```bash
npx skills add xpepper/pr-review-agent-skill/prepare-review-commits
```

No client-specific command wrappers are included. The portable Agent Skill is
the sole source of workflow behavior.

## Dependencies

Core Git is required. GitHub context through `gh` is optional: the skill may
use it to infer intent or a PR base when available, but must preserve its
defined behavior without it.

## Rationale

The new skill serves the same users, delivery format, and pull-request workflow
as the repository's existing skills. Keeping it here provides one discovery,
installation, packaging, documentation, and release surface. A separate or
mirrored repository would add ownership and version-drift cost without creating
a meaningful boundary.
