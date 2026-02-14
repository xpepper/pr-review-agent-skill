---
name: ralph-wiggum-loop
description: Use when setting up an external shell loop to address PR review comments one at a time across fresh agent sessions. Provides CODE_REVIEW_PLAN.md template and PR_COMMENTS_PLAN.md state file format for the Ralph Wiggum pattern.
license: MIT
compatibility: Requires gh CLI. Works with any agent that accepts piped instructions (claude -p, codex exec, etc.). PR branch must be checked out locally.
metadata:
  author: Pietro Di Bello
  version: "1.0.0"
allowed-tools: Bash(gh:*)
---

# Ralph Wiggum Loop

## Overview

The [Ralph Wiggum pattern](https://ghuntley.com/ralph/): an external shell loop
that spawns a **fresh agent session per PR comment**. Each invocation reads a
plan file, does exactly one unit of work (triage or fix), then exits. The shell
loop handles repetition.

This avoids context window exhaustion and works with any agent.

## Setup (once per PR)

1. Copy `CODE_REVIEW_PLAN.md` from this skill to your project root:
   ```bash
   cp ~/.claude/skills/ralph-wiggum-loop/CODE_REVIEW_PLAN.md .
   ```

2. Optionally add both files to `.gitignore`:
   ```
   CODE_REVIEW_PLAN.md
   PR_COMMENTS_PLAN.md
   PR_REVIEW_DONE
   .pr-review/
   ```

3. Start the loop:

   **Claude:**
   ```bash
   while [ ! -f PR_REVIEW_DONE ]; do
     cat CODE_REVIEW_PLAN.md | claude -p --dangerously-skip-permissions
   done
   ```

   **Codex:**
   ```bash
   while [ ! -f PR_REVIEW_DONE ]; do
     cat CODE_REVIEW_PLAN.md | codex exec --yolo -
   done
   ```

   **Any agent that accepts stdin:**
   ```bash
   while [ ! -f PR_REVIEW_DONE ]; do
     cat CODE_REVIEW_PLAN.md | <agent-command>
   done
   ```

## How it works

| Iteration | `PR_COMMENTS_PLAN.md` exists? | What the agent does |
|-----------|-------------------------------|---------------------|
| 1st | No | Fetches all PR comments, triages them, writes the file |
| 2nd–N | Yes | Fixes the topmost unresolved comment, marks it done |
| Final | Yes, all resolved | Writes `PR_REVIEW_DONE`, loop terminates |

Each session is minimal: one triage pass or one comment fix.

## State files (in project root)

- `CODE_REVIEW_PLAN.md` — the instruction file (static, copied once)
- `PR_COMMENTS_PLAN.md` — triage + progress state (generated, updated each run)
- `PR_REVIEW_DONE` — written by the agent when all comments are addressed; stops the loop
- `.pr-review/plan-<id>.md` — per-comment plan for non-trivial fixes (deleted after resolution)

## Cleanup

```bash
rm -f CODE_REVIEW_PLAN.md PR_COMMENTS_PLAN.md PR_REVIEW_DONE
rm -rf .pr-review/
```
