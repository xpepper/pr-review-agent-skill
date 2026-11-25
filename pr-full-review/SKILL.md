---
name: pr-full-review
description: Use only when the user explicitly invokes pr-full-review (for example /pr-full-review) to run a full multi-lens PR review (Standards and Spec against the PR body, Balanced Coupling, refactoring, and duplication), classify all findings, and let the user choose whether to fix items locally or post inline review threads on GitHub. Manual-only; do not start it from context relevance. For an interactive file-by-file walkthrough in runtime-flow order, use guided-flow-review; for addressing existing PR review comments, use pr-review-grill or pr-review-loop.
license: MIT
compatibility: Requires git and gh CLI; optional Node 22+ for duplication-review clone detection (jscpd). PR branch must be checked out locally.
metadata:
  author: Pietro Di Bello
  version: "1.0.0"
allowed-tools: Bash
disable-model-invocation: true
---

# PR Full Review

## Trigger

This skill is **manual-only** (`disable-model-invocation: true`): never load or
start it on your own initiative. Run it only when the user invokes it
explicitly, such as `/pr-full-review` or a request that names the skill.

## Boundaries

- Review is **read-only** until the user chooses an action at Step 4. Never edit
  files, create commits, or post comments on GitHub before the user decides.
- Verify every finding directly against local files at `HEAD`, the PR diff, and
  the PR's own CI status. Never assert that code fails compilation, linting, or
  CI when those checks are green.
- Keep `## Standards` and `## Spec` separate in the report so one axis never
  masks the other.
- Respect prior review history: fetch existing review threads before reporting,
  and omit findings that are already open, resolved, or explicitly deferred,
  unless a concrete unaddressed part remains on `HEAD`.
- Never push commits unless the user explicitly asks to push.

## Process

### 1. Identify the PR, spec, and baseline

Collect the PR metadata, CI checks, git range, and existing review threads. Pass
the PR number or URL if the user named one; otherwise use the current branch's
PR:

```bash
gh pr view [pr-number-or-url] --json number,title,body,baseRefName,headRefName,headRefOid,url,state,files,statusCheckRollup
git rev-parse HEAD
git status --porcelain
```

Confirm that `headRefOid` matches local `HEAD` (clone detection and file reads
inspect the checked-out files). If they differ, stop and ask the user before
checking out the PR branch.

Pin the merge-base and capture the diff and commit log:

```bash
base="$(gh pr view [pr-number-or-url] --json baseRefName --jq '.baseRefName')"
git fetch origin "$base"
merge_base="$(git merge-base "origin/$base" HEAD)"
git log "${merge_base}..HEAD" --oneline
git diff "${merge_base}...HEAD" --stat
```

Abort cleanly if the diff is empty.

Fetch existing review threads (including resolution status and all comments) so
follow-up reviews do not duplicate settled threads:

```bash
gh api graphql -f query='
query($owner:String!, $name:String!, $number:Int!) {
  repository(owner:$owner, name:$name) {
    pullRequest(number:$number) {
      reviewThreads(first:100) {
        nodes {
          id
          isResolved
          isOutdated
          path
          line
          originalLine
          comments(first:20) {
            nodes { databaseId author { login } body createdAt }
          }
        }
      }
    }
  }
}' -f owner='{owner}' -f name='{repo}' -F number={pr_number}
```

Use the **PR body** as the default spec unless the user supplied a different
spec file, issue, or document. Discover every repository coding-standards and
agent-guide document (`AGENTS.md`, `CLAUDE.md`, `CODING_STANDARDS.md`,
`CONTRIBUTING.md`, `GLOSSARY.md`, architecture/testing docs, and workspace
guides for every touched package).

Completion criterion for Step 1: PR identity, `HEAD` match, non-empty diff, CI
state, spec source, standards files, and existing review threads are all loaded.

### 2. Run all four review lenses

Read [references/lenses.md](references/lenses.md) and execute all four lenses
against `${merge_base}...HEAD`:

1. **Code Review, Standards axis** (documented repo standards + Fowler smell
   baseline).
2. **Code Review, Spec axis** (PR body or user-supplied spec verified line by
   line against the diff and surrounding code, including Evidence claims and
   edge cases).
3. **Balanced Coupling / Modularity** (strength, socio-technical distance, and
   essential domain volatility of the boundaries created or changed by this PR).
   Scope this lens strictly to the PR's changed boundaries; never trigger an
   interactive whole-codebase questionnaire.
4. **Code Refactor Review + Duplication Review** (bidirectional reuse search by
   concept, shape, and neighborhood; consistency, composition, slop, minimality;
   plus `duplication-review`'s `clones.mjs` scan with every touched family
   inspected and ruled `Extract` or `Tolerate`).

When the runtime supports parallel subagents, run **Standards**, **Spec**, and
**Balanced Coupling** in parallel with fresh context windows so they do not
pollute one another, while running **Code Refactor Review** and **Duplication
Review** alongside them.

When sibling skills are installed (`code-review`, `balanced-coupling`,
`code-refactor-review`, `duplication-review`), honor their latest rules; use
[references/lenses.md](references/lenses.md) as the authoritative fallback when
any companion skill is absent.

Completion criterion for Step 2: all four lenses have completed, every touched
clone family has been read and ruled, and every repo standards file has been
checked.

### 3. Cross-verify, deduplicate, and classify

Before presenting anything:

1. Verify every candidate finding against the actual files at `HEAD` and the
   PR diff hunks. Drop speculative claims, false positives, and anything green
   CI or tooling already enforces.
2. Compare against the existing PR review threads from Step 1. Drop items
   already open or resolved and explicitly settled. Keep an item only if a
   concrete part of it remains unaddressed on `HEAD`, and state that link
   explicitly.
3. Deduplicate overlapping findings across lenses (for example, a boundary leak
   flagged by both Balanced Coupling and Refactor becomes one numbered item in
   the classified table, crediting both lenses), while preserving the separate
   `## Standards` and `## Spec` sections.
4. Classify each finding with:
   - **Class**: `Bug`, `Security`, `Question`, `Design`, `Cleanup`, `Test`, or
     `Duplication`.
   - **Severity**: `high`, `medium`, or `low`.
   - **Recommended action**: `fix now`, `post thread` (for product questions,
     design trade-offs, or review handoff), or `defer` (pre-existing or
     low-value follow-up).
   - **Inline candidate**: mark whether the finding is high-signal enough for an
     inline PR thread and note its exact `file:line` inside a `RIGHT` diff hunk
     (or the triggering diff line if the issue lives outside the diff).

### 4. Present the report and stop at the decision gate

Print the complete review in chat with these sections:

1. **Header**: PR number/link, reviewed SHA (`headRefOid`), base merge-base,
   diff stats, and CI status.
2. **Classified Findings** (compact numbered table, highest severity first):
   `| # | Class (severity) | Location | Lenses | Summary | Suggested action |`
3. **`## Standards`** and **`## Spec`** kept strictly separate (never merged or
   reranked across the two axes), ending with a one-line summary giving total
   findings and the worst issue within each axis.
4. **`## Balanced Coupling`**: concise boundary map and unbalanced + volatile
   findings (or a one-line note if none).
5. **`## Code Refactor Review`**: verdict (`clean`, `mostly clean`, or
   `needs cleanup`), prioritized findings, and `Outside this diff` when
   applicable.
6. **`## Duplication Review`**: `jscpd` totals + renamed count, every touched
   family (`Extract` first, then `Tolerate`), and `largest` bystanders plus the
   count of the rest.

**Stop here and ask the user how to proceed.** When an interactive question tool
is available, offer these options (otherwise ask in plain text):

- **Fix selected items locally now**: implement chosen findings directly on this
  branch with focused commits (no GitHub threads needed first).
- **Post selected items as inline review threads on the PR**: submit one atomic
  `COMMENT` review on GitHub for the chosen findings.
- **Split (fix some locally, post others as PR threads)**: for example, fix
  clear bugs/cleanups locally and post product questions or design trade-offs on
  the PR.
- **Done (review only)**: leave code and GitHub untouched.

Wait for the user's explicit selection before editing files or calling any
GitHub write API.

### 5. Execute the chosen action(s)

Read [references/actions.md](references/actions.md) and execute only what the
user approved:

- **Local fixes**: run repository safeguards, protect unrelated dirty files,
  implement each approved item (or cascade) in one focused Conventional Commit
  with tests, re-run safeguards after each fix, and never push unless asked.
- **Inline PR threads**: verify every target `(path, line)` sits inside a
  `RIGHT` diff hunk, submit one atomic `COMMENT` review on `headRefOid` via a
  JSON file input, and verify the posted threads via `GET` (never re-POST).
- **Split**: apply local fixes first if the user wants threads only for
  unaddressed questions/design items, or post threads only on unchanged lines
  matching `headRefOid`.

## Do Not

- Start this skill unprompted without explicit user invocation.
- Edit files, commit, push, or post GitHub reviews/comments before Step 4
  approval.
- Merge or rerank `## Standards` and `## Spec` into a single combined axis.
- Trigger an interactive whole-codebase modularity wizard during Step 2.
- Re-open findings already settled in resolved PR review threads.
- Claim a build, lint, or test failure without evidence from CI or a local run.
- Post inline threads on lines outside the PR diff hunks, or re-POST to verify.
