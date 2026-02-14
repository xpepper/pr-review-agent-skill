# Copilot Review Loop

An [Agent Skills](https://agentskills.io) skill that automates iterative
GitHub Copilot review loops within a single agent session: trigger Copilot
review, address its feedback one comment at a time, repeat up to 2 cycles.

## What it does

1. Discovers project safeguards from project conventions and runs them
2. Triggers a GitHub Copilot review on the PR
3. Waits for Copilot to complete, then collects its unresolved comments
4. Addresses each comment one at a time: triage → test → fix → test → commit → reply → resolve
5. Re-triggers Copilot review and repeats (max 2 cycles)
6. Posts a final PR summary

If the `pr-review-loop` skill is also installed, delegates the inner loop to it.

## Key property: resumable

Can be interrupted and restarted in a fresh context window at any point
without losing progress.

## Prerequisites

- `gh` CLI (required)
- `gh-copilot-review` extension (recommended):
  ```bash
  gh extension install ChrisCarini/gh-copilot-review
  ```
- `pr-review-loop` skill (optional — enhances inner loop)
- PR branch checked out locally

## Install

```bash
npx skills add xpepper/pr-review-agent-skill/copilot-review-loop -a claude-code
```

## Usage

Once installed, describe what you want — the agent activates the skill automatically:

```
Request a Copilot review on this PR and address the feedback
```
```
Trigger a GitHub Copilot review and fix the issues it finds
```

You can also invoke it explicitly:

```
Run copilot-review-loop on PR #42
```
```
Use copilot-review-loop to get and address Copilot's review comments
```
