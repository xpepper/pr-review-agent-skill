# Guided Flow Review

An [Agent Skills](https://agentskills.io) skill for walking through a pull
request (your own draft or someone else's) or other identifiable change
together, file by file, and collecting the outcome in a review TODO.

Instead of reading files in diff order, the skill follows the path the software
actually runs, outside in: each flow is walked depth-first from its trigger or
entry point through wiring, configuration, and core behavior down to adapters,
with tests beside the code they exercise; unreachable files, packaging, and
documentation come last. Each proposed step names the call or registration
that reaches it, so you can check the order. Each step discusses what looks right and
what could improve, and ends with an explicit decision on where each finding
goes.

## What it does

1. Identifies and pins the reviewed PR, branch, commit range, or working-tree
   change.
2. Reads the project's instructions so findings follow its conventions.
3. Derives and presents an outside-in, top-down review order, one flow at a
   time.
4. Reviews one file or tightly coupled group at a time.
5. Presents evidenced, weighted findings with a recommended route.
6. Uses the runtime's native interaction when available, with a portable text
   fallback, so you can route findings or ask questions before deciding.
7. Stops after routing each step and waits for you to ask more or explicitly
   move to the named next step.
8. Maintains a disposable, resumable review TODO at the repository root.
9. Closes with a summary and hands the TODO over: address items one by one
   (as focused, verified commits), share it with the team, or turn items into
   tickets. Fixing is opt-in.

## When to use it

Use it when you want to understand and improve a change together.

The skill is **manual-only**. Its frontmatter sets
`disable-model-invocation: true`, so the agent never starts it on its own, even
when a request looks like a review. Invoke it yourself, optionally with the
target and where to start:

```text
/guided-flow-review
```

```text
/guided-flow-review PR #42, follow the flow from the cronjob through main
```

```text
/guided-flow-review my current working-tree changes
```

On runtimes that ignore `disable-model-invocation`, the skill falls back to its
description, which also limits activation to explicit requests that name the
skill:

```text
Use guided-flow-review on this branch
```

> `disable-model-invocation` is honoured by Claude Code. Agents that do not
> support the field ignore it and fall back to the description.

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
the skill uses `GUIDED_REVIEW_TODO.md` instead.

## Safety properties

- Reviews read-only: code changes only when you ask to fix an item. Approving
  a route records it in the TODO rather than editing code; fix requests apply
  strictly to that item alone.
- Pins the base SHA or exact comparison so a moving branch does not change the
  review silently.
- Never copies secret values into review notes or implementation prompts.
- When fixing, keeps unrelated work, local environment files, and the review
  TODO on a never-stage list, stages explicit paths only, and verifies each
  focused commit before continuing.
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
