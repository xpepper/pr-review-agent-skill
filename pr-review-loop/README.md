# PR Review Loop

An [Agent Skills](https://agentskills.io) skill that automates iterative PR comment resolution
with an opinionated, resumable workflow.

## What it does

1. Discovers project safeguards (tests, linting, compilation) from project conventions
2. Collects all unresolved PR comments from any reviewer
3. Triages each comment: MUST_FIX, SHOULD_FIX, PARK, or OUT_OF_SCOPE
4. Addresses comments one at a time: test → fix → test → commit → reply → resolve
5. Posts a final PR summary when done

## Key property: resumable

The skill can be interrupted and restarted in a fresh context window at any point
without losing progress. Each fix is committed and pushed before moving on.

## Prerequisites

- `gh` CLI (recommended) — falls back to GitHub REST API if unavailable
- PR branch checked out locally

## Install

```bash
npx skills add xpepper/pr-review-agent-skill/pr-review-loop -a claude-code
```

## Optional: Perplexity for deep research

If you have the [Perplexity Web Research skill](https://github.com/xpepper/perplexity-agent-skill)
installed, the agent will use it for research-heavy triage decisions.
