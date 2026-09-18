# Guided Flow Review

An [Agent Skills](https://agentskills.io) skill for reviewing a pull request or
other identifiable change collaboratively with its author.

Instead of reading files in diff order, the skill follows the path the software
actually runs: trigger or entry point, wiring, configuration, core behavior,
tests, packaging, and documentation. Each review step ends with an explicit
decision before any code changes.

## What it does

1. Identifies and pins the reviewed PR, branch, commit range, or working-tree
   change.
2. Reads repository safeguards and separates reviewed changes from unrelated
   author work.
3. Derives and presents a runtime-flow review order.
4. Reviews one file or tightly coupled group at a time.
5. Presents evidenced, weighted findings with a recommended route.
6. Lets the author choose whether to fix, record, or drop each finding.
7. Maintains a disposable, resumable review TODO at the repository root.
8. Applies accepted fixes as focused, verified commits when the review target
   has a safe committed baseline.
9. Closes with validation results, remaining questions, and suggested PR
   description updates.

## When to use it

Use it when you want to understand and improve a change together:

```text
We are reviewing this PR together. Follow the flow from the cronjob through
main and review each changed file with me.
```

```text
Walk me through this branch one runtime step at a time. Do not change anything
until I decide how to route each finding.
```

```text
Review my current working-tree changes with me and keep a TODO of our decisions.
```

For a fast batch review, use a batch code-review workflow. To discuss existing
reviewer comments, use
[`pr-review-grill`](../pr-review-grill/README.md). To process approved review
comments efficiently, use
[`pr-review-loop`](../pr-review-loop/README.md).

## Durable review state

The skill creates an untracked, disposable `TODO.md` at the repository root. It
records:

- findings that must be fixed before merge;
- refactorings and missing tests;
- domain questions and their owners;
- separate-ticket follow-ups;
- completed fixes and commit subjects;
- review progress in runtime order.

If `TODO.md` is already a tracked project file or belongs to another purpose,
the skill uses `GUIDED_REVIEW_TODO.md` instead. It asks before adding the review
file to the clone's local Git exclude file (`info/exclude`).

## Safety properties

- Pins the base SHA or exact comparison so a moving base branch does not change
  the review silently.
- Scans staged, unstaged, and untracked files before edits.
- Keeps unrelated work, local environment files, and review state on a
  never-stage list.
- Never copies secret values into review notes or implementation prompts.
- Uses edit-only mode for uncommitted changes unless the author establishes a
  committed baseline.
- Requires explicit staging and verifies each focused commit before continuing.
- Does not push, edit the PR, publish a summary, or create tickets unless asked.

## Install

```bash
npx skills add xpepper/pr-review-agent-skill/guided-flow-review
```

## Requirements

- Git
- An interactive user who can route findings
- [`gh`](https://cli.github.com/) when reviewing a GitHub pull request
- The repository's documented formatter, tests, linter, and completion command
  when accepted findings are fixed
