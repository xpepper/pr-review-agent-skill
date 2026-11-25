# PR Full Review

An [Agent Skills](https://agentskills.io) skill that runs a comprehensive
multi-lens review of a GitHub pull request, classifies every verified finding,
and stops at a decision gate so you can either fix selected issues locally right
away or post them as inline review threads on GitHub.

## Install

```bash
npx skills add xpepper/pr-review-agent-skill/pr-full-review
```

For global installation across your agents:

```bash
npx skills add xpepper/pr-review-agent-skill/pr-full-review --global
```

## Usage

This skill is **manual-only** (`disable-model-invocation: true`), so the agent
never starts it unprompted. Invoke it explicitly:

```text
/pr-full-review
```

Review a specific pull request or supply an alternate spec source:

```text
/pr-full-review #123
```

```text
/pr-full-review https://github.com/org/repo/pull/123 using docs/spec.md as the spec
```

## What it runs

All four lenses run against the merge-base diff of the checked-out PR branch
(using parallel fresh-context subagents where supported so review axes do not
bias each other):

1. **Standards (Code Review, Axis 1)**: checks every repository standards and
   agent-guide document (`AGENTS.md`, `CLAUDE.md`, `GLOSSARY.md`, testing and
   code-pattern guides) plus the Fowler code-smell baseline, keeping hard
   violations separate from judgement calls.
2. **Spec (Code Review, Axis 2)**: verifies the diff and surrounding code
   line by line against the PR body (or a user-supplied spec) for missing or
   partial requirements, scope creep, edge-case bugs, and Evidence accuracy.
   Reported separately from `## Standards`.
3. **Balanced Coupling / Modularity**: evaluates boundaries created or changed
   by the PR across integration strength, socio-technical distance, and
   essential domain volatility, flagging only unbalanced and volatile coupling
   or low cohesion.
4. **Code Refactor Review + Duplication Review**: searches the codebase in both
   directions for reuse opportunities, consistency, composition, and slop, and
   runs `duplication-review`'s `jscpd` clone scan (`clones.mjs`) when installed,
   ruling every touched clone family `Extract` or `Tolerate`.

Before reporting, every finding is cross-verified against local `HEAD`, the PR's
CI status, and existing PR review threads so already-settled threads and false
positives are filtered out.

## Decision gate and actions

The review prints a compact numbered **Classified Findings** table followed by
the per-lens reports, then **stops and asks** how you want to proceed:

- **Fix selected items locally now**: apply chosen fixes directly on the branch
  with repository safeguards and one focused Conventional Commit per item (no
  need to publish GitHub threads first).
- **Post selected items as inline review threads**: submit one atomic `COMMENT`
  review on GitHub anchored to verified `RIGHT`-side diff hunk lines, and verify
  every posted thread via `GET`.
- **Split**: fix clear bugs or cleanups locally and post open product questions
  or design trade-offs as PR threads.
- **Done (review only)**: leave both the repository and GitHub untouched.

## Companion skills

`pr-full-review` works standalone using its bundled
[`references/lenses.md`](references/lenses.md), and integrates with these
optional skills when installed:

- `code-review` (two-axis Standards + Spec)
- `balanced-coupling` (Balanced Coupling model reference)
- `code-refactor-review` (refactoring and slop lenses)
- `duplication-review` (bundled `scripts/clones.mjs` + `jscpd` scanner)

## Prerequisites

- Git, with the PR branch checked out locally.
- [`gh` CLI](https://cli.github.com/) authenticated to GitHub.
- Optional: Node 22+ and `duplication-review` installed for automated `jscpd`
  clone detection.
