# PR Review Grill

An [Agent Skills](https://agentskills.io) skill for working through pull
request review feedback collaboratively, one comment at a time.

## What it does

1. Discovers repository safeguards and confirms a healthy baseline.
2. Collects unresolved inline and top-level PR feedback.
3. Presents one comment with codebase evidence and a provisional assessment.
4. Grills the premise with the user until the classification and action are
   explicit.
5. Persists every decision in `.pr-review/triage.json`.
6. Processes approved fixes one at a time with safeguards, focused commits,
   replies, and resolution.
7. Reports parked, rejected, and clarification items without silently changing
   them.

## When to use it

Use this skill when you want to discuss review feedback before acting:

```text
Walk through every PR comment with me one at a time and grill the reasoning.
```

```text
Use pr-review-grill on PR #42; don't start coding until we've debated each
comment.
```

For a faster batch triage, use `pr-review-loop` instead.

## Install

```bash
npx skills add xpepper/pr-review-agent-skill/pr-review-grill
```

## Prerequisites

- `gh` CLI or another GitHub client
- `jq`
- The PR branch checked out locally

The skill writes resumable local state to `.pr-review/triage.json`. The
directory must be gitignored.
