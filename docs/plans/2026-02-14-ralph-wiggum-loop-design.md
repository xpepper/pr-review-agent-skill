# Ralph Wiggum Loop — Design

**Date**: 2026-02-14
**Status**: Approved

## Context

This is **Skill 2** in the `pr-review-agent-skill` repo. It builds conceptually on the approach of Skill 1 (PR Review Loop) but is fully independent — users can install either skill without the other. If Skill 1 is installed, Skill 2 delegates its inner loop to it.

The name references the Simpsons character Ralph Wiggum: the agent keeps asking Copilot "is this better?" and iterating until Copilot is happy (or until it gives up after 2 cycles).

## Purpose

Automate an iterative Copilot-driven review loop: trigger a Copilot review, address its feedback one comment at a time, then re-trigger Copilot to review again. Repeat until all critical issues are resolved or the iteration limit is reached.

## Relationship to Skill 1

| Aspect | PR Review Loop (Skill 1) | Ralph Wiggum Loop (Skill 2) |
|---|---|---|
| Comment source | Any reviewer (human or bot) | GitHub Copilot only |
| Trigger | Existing comments on the PR | Agent triggers Copilot review first |
| Inner loop | Is the inner loop | Delegates to Skill 1 if available |
| Iteration | Single pass | Up to 2 Copilot review cycles |

## Prerequisites

- `gh` CLI (required)
- `gh-copilot-review` extension (recommended):
  ```bash
  gh extension install ChrisCarini/gh-copilot-review
  ```
  Fallback if not installed: `gh pr review --request copilot`
- `pr-review-loop` skill (optional — if installed, inner loop is delegated to it)

## Process

### Step 1 — Pre-flight

Same as Skill 1: inspect the project for safeguard conventions (`CLAUDE.md`, `AGENTS.md`, `Makefile`, CI workflows, `README`). Run all discovered safeguards. Stop and report if any fail.

### Step 2 — Outer loop (max 2 iterations)

Repeat up to 2 times:

#### 2a. Request Copilot review

Preferred (requires `gh-copilot-review` extension):
```bash
gh copilot-review [<number> | <url>]
```

Fallback:
```bash
gh pr review --request copilot
```

#### 2b. Wait for Copilot to complete

Poll the PR until new review comments appear from `copilot[bot]`. If no new comments appear within a reasonable timeout, stop and report — do not proceed blindly.

#### 2c. Collect unresolved Copilot comments

Fetch all unresolved PR comments authored by `copilot[bot]`. Ignore comments from human reviewers (those belong to Skill 1's domain).

#### 2d. Address comments — inner loop

Process one comment at a time, in triage order (MUST_FIX first, then SHOULD_FIX).

**If `pr-review-loop` skill is available:**
Invoke it, scoped to the Copilot comments collected in step 2c.

**If not available:**
Follow the same one-at-a-time process:
1. Triage the comment (MUST_FIX / SHOULD_FIX / PARK / OUT_OF_SCOPE)
2. Assess complexity — trivial: fix directly; non-trivial: write plan to `.pr-review/plan-<comment-id>.md`
3. Run safeguards (confirm green baseline)
4. Fix or park
5. Run safeguards again
6. Commit & push
7. Reply to the comment (fix description, deferral, or rejection)
8. Resolve the comment on GitHub
9. Delete plan file if created

#### 2e. Check stop conditions

Stop iterating if any of:
- No MUST_FIX Copilot comments remain
- Only OUT_OF_SCOPE Copilot comments remain
- Max 2 iterations reached

### Step 3 — Summary

Post a final PR comment summarising across all iterations:
- What was fixed (with commit references)
- What was parked (with reasoning)
- What was rejected (with reasoning)
- How many Copilot review cycles were completed

## Resumability

Same property as Skill 1: the skill can be interrupted and restarted at any point.

On restart:
1. Run pre-flight
2. Check for existing `.pr-review/plan-*.md` — if found, continue mid-fix from there
3. Re-fetch unresolved Copilot comments — already-resolved ones won't appear
4. Continue the outer loop from the current iteration

## State Directory

`.pr-review/` at the repo root (same as Skill 1).
- `plan-<comment-id>.md` — plan for the comment currently in progress

## Next Steps

- Implement Skill 1 (PR Review Loop) first — it is the foundational primitive
- Then implement Skill 2 (this skill), adding the Copilot trigger and outer loop
