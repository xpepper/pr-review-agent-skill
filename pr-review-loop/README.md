# PR Review Loop

An [Agent Skills](https://agentskills.io) skill that automates iterative PR comment resolution
with an opinionated, resumable workflow.

## What it does

1. Discovers project safeguards (tests, linting, compilation) from project conventions
2. Collects all unresolved PR comments from any reviewer
3. Triages each comment: MUST_FIX, SHOULD_FIX, PARK, OUT_OF_SCOPE, or NEEDS_CLARIFICATION
4. Presents the triage and waits for your go-ahead before changing anything
5. Addresses comments one at a time: test → fix → test → commit → reply → resolve
6. Updates the PR body if the new commits drifted its scope
7. Posts a final PR summary when done

## Execution modes

### Normal mode

The default workflow processes the approved queue in the current agent session.
It remains resumable through focused commits, pushed progress, and re-fetching
GitHub state.

### Experimental handoff mode

Use handoff mode when you want a fresh agent context for each narrowly defined
scope:

```text
/pr-review-loop --handoff
```

The first session triages all current feedback, records your approval in a
gitignored `.pr-review/HANDOFF.md`, and stops. Each later session:

1. re-fetches GitHub and reconciles new or changed feedback;
2. delta-triages feedback changes, or completes exactly one approved comment or
   atomic cascade;
3. updates the handoff and reports how many items are addressed, still
   actionable, awaiting triage, or awaiting a reviewer;
4. stops with the exact `/pr-review-loop --handoff` command and next scope.

Final PR-body and summary work happens in its own fresh session. The handoff
is retained through finalization so later reviewer feedback can reopen the
workflow; keeping it also preserves the queue, remote comment IDs, and summary
history. After the cycle is complete, the agent explains that deleting the
handoff drops those records, then asks whether you want to delete only
`.pr-review/HANDOFF.md` (the `.pr-review/logs/` directory and any other local
review state are left untouched); cleanup never happens without your
confirmation.

Handoff mode is manual and sequential: explicitly invoke it in every fresh
session and do not run two handoff agents concurrently in the same worktree.

## Key property: resumable

The skill can be interrupted and restarted in a fresh context window at any point
without losing progress. Each fix is committed and pushed before moving on.

## Prerequisites

- `gh` CLI (recommended).
- PR branch checked out locally

## Install

```bash
npx skills add xpepper/pr-review-agent-skill/pr-review-loop
```

## Usage

Once installed, just describe what you want — the agent activates the skill automatically:

```
Address all open review comments on this PR
```
```
Work through the code review feedback on PR #42
```
```
Fix the review comments left by @alice on this pull request
```

You can also invoke it explicitly by naming the skill:

```
Use pr-review-loop on PR #123
```
```
Run the PR review loop on this branch
```

To use experimental handoff mode:

```text
/pr-review-loop --handoff
```

or:

```text
Continue the PR review in handoff mode
```

### Install the experimental version from a PR branch

Replace `<pr-branch>` with the pull request's head branch:

```bash
npx skills add \
  "xpepper/pr-review-agent-skill#<pr-branch>@pr-review-loop" \
  -a claude-code \
  --yes
```

The quoted `#<pr-branch>@pr-review-loop` source pins the Git branch, including
branch names containing `/`, and selects only the `pr-review-loop` skill.

## Optional: Perplexity for deep research

If you have the [Perplexity Web Research skill](https://github.com/xpepper/perplexity-agent-skill) installed, the agent will use it for research-heavy triage decisions.
