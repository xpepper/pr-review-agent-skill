# Ralph Wiggum Loop

An [Agent Skills](https://agentskills.io) skill implementing the
[Ralph Wiggum pattern](https://ghuntley.com/ralph/): an external shell loop that
spawns a fresh agent session per PR comment. Each invocation does exactly one unit
of work (triage or fix one comment), then stops. The shell loop handles repetition.

Works with any agent that accepts piped instructions.

## Why this pattern?

- Each session is minimal — no context window exhaustion
- Stateless agent, stateful files — resume after any failure by restarting the loop
- Agent-agnostic — works with Claude, Codex, Cursor, or any future agent
- Transparent — `PR_COMMENTS_PLAN.md` shows exactly what's done and what's pending

## Usage

This skill is not invoked via chat. You run a shell loop in your terminal —
the loop is the invocation:

```bash
# Claude
while [ ! -f PR_REVIEW_DONE ]; do
  cat CODE_REVIEW_PLAN.md | claude -p --dangerously-skip-permissions
done

# Codex
while [ ! -f PR_REVIEW_DONE ]; do
  cat CODE_REVIEW_PLAN.md | codex exec --yolo -
done
```

See **Setup** below to get `CODE_REVIEW_PLAN.md` into your project first.

## Setup

### 1. Install the skill

```bash
npx skills add xpepper/pr-review-agent-skill/ralph-wiggum-loop -a claude-code
```

### 2. Copy the plan file to your project root

```bash
cp ~/.claude/skills/ralph-wiggum-loop/CODE_REVIEW_PLAN.md .
```

### 3. Optionally gitignore the working files

```gitignore
CODE_REVIEW_PLAN.md
PR_COMMENTS_PLAN.md
PR_REVIEW_DONE
.pr-review/
```

### 4. Run the loop

```bash
# Claude
while [ ! -f PR_REVIEW_DONE ]; do
  cat CODE_REVIEW_PLAN.md | claude -p --dangerously-skip-permissions
done

# Codex
while [ ! -f PR_REVIEW_DONE ]; do
  cat CODE_REVIEW_PLAN.md | codex exec --yolo -
done
```

## How it works

| Iteration | What the agent does |
|-----------|---------------------|
| 1st | Fetches all PR comments, triages them, writes `PR_COMMENTS_PLAN.md` |
| 2nd–N | Fixes the topmost unresolved comment (MUST_FIX first, then SHOULD_FIX) |
| Final | Writes `PR_REVIEW_DONE` → loop terminates |

## Prerequisites

- `gh` CLI authenticated to GitHub
- PR branch checked out locally

## Cleanup

```bash
rm -f CODE_REVIEW_PLAN.md PR_COMMENTS_PLAN.md PR_REVIEW_DONE
rm -rf .pr-review/
```
