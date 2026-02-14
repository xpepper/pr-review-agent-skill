# PR Review Loop — Design

**Date**: 2026-02-14
**Status**: Approved

## Context

This document describes the design for **Skill 1: PR Review Loop**, the first of two related agent skills to be hosted in a new dedicated repo (`pr-review-agent-skill`). Skill 2 (Ralph Wiggum Loop) will be designed separately and will build on this skill.

## Repo Structure

```
pr-review-agent-skill/
├── README.md
├── package-skill.sh
├── pr-review-loop/
│   ├── SKILL.md
│   └── references/
│       └── triage-guide.md
└── ralph-wiggum-loop/
    ├── SKILL.md
    └── references/
```

Each skill installs independently via the Agent Skills CLI:

```bash
npx skills add xpepper/pr-review-agent-skill/pr-review-loop -a claude-code
npx skills add xpepper/pr-review-agent-skill/ralph-wiggum-loop -a claude-code
```

## Skill 1: PR Review Loop

### Purpose

Automate the process of addressing PR review comments one at a time, with an opinionated and resumable workflow. Works with comments from any reviewer (human or bot).

### Prerequisites

- `gh` CLI (recommended). Falls back to GitHub REST API if unavailable.

### Process

#### Step 1 — Pre-flight

Inspect the project for safeguard conventions by checking:
- `CLAUDE.md`, `AGENTS.md`
- `Makefile`
- CI workflows (`.github/workflows/`)
- `README`

Run all discovered safeguards (tests, compilation, linting, formatting, etc.). Stop and report if any fail. Do not proceed on a broken baseline.

#### Step 2 — Collect

Fetch all unresolved PR comments via `gh` CLI, or the GitHub REST API as fallback. Includes comments from any reviewer (human or bot).

#### Step 3 — Triage

Classify each comment into one of four categories:

| Category | Meaning |
|---|---|
| `MUST_FIX` | Blocking issue; must be addressed before the PR can merge |
| `SHOULD_FIX` | Non-blocking but worth addressing in this PR |
| `PARK` | Valid point, deferred to a future issue/PR |
| `OUT_OF_SCOPE` | Does not apply to this PR; rejected with explanation |

If Perplexity is available, use it for research-heavy triage decisions (e.g., checking whether a pattern is idiomatic in the language/framework).

#### Step 4 — Process one comment at a time

Process in order: `MUST_FIX` first, then `SHOULD_FIX`.

For each comment:

1. **Assess complexity**:
   - Trivial (e.g., renaming, small refactor): fix directly, no plan needed
   - Non-trivial: enter a plan phase first; save plan to `.pr-review/plan-<comment-id>.md`

2. **Run safeguards** — confirm green baseline before touching any code

3. **Fix or park**:
   - Fix: implement the change
   - Park: write reasoning for deferral/rejection, no code change

4. **Run safeguards again** — confirm completion

5. **Commit & push**

6. **Reply to the PR comment** — explain what was done (fix description, deferral reasoning, or rejection rationale)

7. **Resolve the comment** on GitHub

8. **Delete the plan file** if one was created

#### Step 5 — Stop condition

Stop when no `MUST_FIX` or `SHOULD_FIX` comments remain (only `PARK` or `OUT_OF_SCOPE` left).

#### Step 6 — Summary

Post a final PR comment summarising:
- What was fixed (with commit references)
- What was parked (with reasoning)
- What was rejected (with reasoning)

### Key Property: Resumability

Every step is self-conclusive. The skill is designed to be interrupted at any point and restarted in a fresh context window without losing progress:

- Unresolved comments are always re-fetched from GitHub on startup
- Each fix is committed and pushed before moving to the next comment
- Plan files (`.pr-review/plan-<comment-id>.md`) persist on disk so in-progress work survives interruptions
- The agent re-reads any existing plan file and continues from where it left off

### State Directory

`.pr-review/` at the repo root. Used for:
- `plan-<comment-id>.md` — plan file for the comment currently being addressed (deleted after the comment is resolved)

## Next Steps

- Build Skill 1 (`pr-review-loop`)
- Design Skill 2 (`ralph-wiggum-loop`), which uses Skill 1 as its inner loop and adds Copilot-triggered iteration
