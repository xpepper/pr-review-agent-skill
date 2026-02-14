# Ralph Wiggum Loop — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add the `ralph-wiggum-loop` skill to the `pr-review-agent-skill` repo — an automated Copilot-driven review loop that triggers Copilot review, addresses its feedback one comment at a time, and repeats up to 2 cycles.

**Architecture:** A single `SKILL.md` drives the agent. It wraps the inner loop from `pr-review-loop` (delegating to it if installed, otherwise running the same process itself) in an outer loop that re-triggers GitHub Copilot review after each pass. A reference doc covers the `gh-copilot-review` extension setup.

**Tech Stack:** `gh` CLI, `gh-copilot-review` extension (`ChrisCarini/gh-copilot-review`), git, Agent Skills standard (SKILL.md + references/)

---

> **Note:** This plan assumes Skill 1 (`pr-review-loop`) is already implemented in the repo. Complete that plan first before starting this one.

---

## Task 1: Write the gh-copilot-review reference guide

**Files:**
- Create: `ralph-wiggum-loop/references/gh-copilot-review-guide.md`

**Step 1: Create the references directory**

```bash
mkdir -p ralph-wiggum-loop/references
```

**Step 2: Write the reference guide**

```markdown
# gh-copilot-review Extension Guide

## Purpose

This guide explains how to trigger a GitHub Copilot review from the CLI,
which is the key mechanism powering the Ralph Wiggum Loop.

## Recommended: gh-copilot-review extension

Install once:
```bash
gh extension install ChrisCarini/gh-copilot-review
```

Trigger a Copilot review:
```bash
# By PR number
gh copilot-review 42

# By PR URL
gh copilot-review https://github.com/owner/repo/pull/42

# Current branch's PR (detect from git)
gh copilot-review
```

## Fallback: gh pr review --request

If the extension is not installed:
```bash
gh pr review --request copilot
```

Note: This may not work on all GitHub plans. The extension is more reliable.

## Detecting which to use

Check if the extension is installed:
```bash
gh extension list | grep copilot-review
```

If it appears in the output, use `gh copilot-review`. Otherwise fall back to `gh pr review --request copilot`.

## Waiting for Copilot to complete

After triggering, Copilot review takes 30–120 seconds. Poll until new
`copilot[bot]` review comments appear:

```bash
# Count current Copilot comments
gh api repos/{owner}/{repo}/pulls/{pr}/comments \
  --jq '[.[] | select(.user.login == "copilot[bot]") | select(.resolved == false)] | length'
```

Poll every 15 seconds. After 3 minutes with no new comments, stop and report timeout.

## Identifying Copilot comments

Filter by reviewer login `copilot[bot]`:
```bash
gh api repos/{owner}/{repo}/pulls/{pr}/comments \
  --jq '.[] | select(.user.login == "copilot[bot]") | select(.resolved == false)'
```
```

**Step 3: Commit**

```bash
git add ralph-wiggum-loop/references/gh-copilot-review-guide.md
git commit -m "docs(ralph-wiggum-loop): add gh-copilot-review reference guide"
```

---

## Task 2: Write the SKILL.md

**Files:**
- Create: `ralph-wiggum-loop/SKILL.md`

**Step 1: Write SKILL.md**

```markdown
# Ralph Wiggum Loop

## Purpose

Automate an iterative Copilot-driven review loop: trigger a GitHub Copilot
review, address its feedback one comment at a time, then re-trigger Copilot
to review again. Repeat up to 2 cycles until all critical issues are resolved.

Named after Ralph Wiggum: the agent keeps asking Copilot "is this better now?"
until it's satisfied — or gives up after 2 tries.

## Prerequisites

- `gh` CLI (required)
- `gh-copilot-review` extension (recommended — see `references/gh-copilot-review-guide.md`)
  ```bash
  gh extension install ChrisCarini/gh-copilot-review
  ```
  Fallback if not installed: `gh pr review --request copilot`
- `pr-review-loop` skill (optional — if installed, the inner loop is delegated to it)
- The PR branch must be checked out locally

## Process

### Step 1 — Pre-flight

Inspect the project for safeguard conventions by checking these files (if they exist):
- `CLAUDE.md`, `AGENTS.md`
- `Makefile`
- `.github/workflows/`
- `README.md`

Identify all required safeguards (tests, compilation, linting, formatting, etc.).
Run all of them. If any fail, stop immediately and report — do not proceed.

### Step 2 — Outer loop (max 2 iterations)

Repeat up to 2 times:

#### 2a. Request Copilot review

Check if `gh-copilot-review` extension is installed:
```bash
gh extension list | grep copilot-review
```

If installed (preferred):
```bash
gh copilot-review [<number> | <url>]
```

If not installed (fallback):
```bash
gh pr review --request copilot
```

#### 2b. Wait for Copilot to complete

Read `references/gh-copilot-review-guide.md` for the polling approach.

Record the current count of unresolved `copilot[bot]` comments before triggering.
Poll every 15 seconds until new comments appear. If no new comments after 3 minutes,
stop and report timeout — do not proceed.

#### 2c. Collect unresolved Copilot comments

Fetch all unresolved comments authored by `copilot[bot]`. Ignore comments from
human reviewers (those are handled by the `pr-review-loop` skill).

```bash
gh api repos/{owner}/{repo}/pulls/{pr}/comments \
  --jq '.[] | select(.user.login == "copilot[bot]") | select(.resolved == false)'
```

If there are no unresolved Copilot comments, stop — nothing to do.

#### 2d. Address comments — inner loop

**If `pr-review-loop` skill is available:**
Invoke the `pr-review-loop` skill, passing only the Copilot comments collected
in step 2c as the scope. It will handle triage, one-at-a-time fixes, and replies.

**If `pr-review-loop` skill is NOT available:**
Follow this process for each comment, one at a time (MUST_FIX first, then SHOULD_FIX):

Triage categories (see below):
- MUST_FIX: blocking correctness issue, security flaw, or broken build
- SHOULD_FIX: non-blocking improvement worth addressing
- PARK: valid but out of scope for this PR — reply with reasoning, open follow-up issue
- OUT_OF_SCOPE: does not apply — reply with rejection reasoning

For each MUST_FIX and SHOULD_FIX comment:

1. **Assess complexity:**
   - Trivial (rename, small fix): fix directly
   - Non-trivial: write plan to `.pr-review/plan-<comment-id>.md` first

2. **Run safeguards** — all must pass before touching code

3. **Fix or park the comment**

4. **Run safeguards again** — all must pass

5. **Commit and push:**
   ```bash
   git add <changed files>
   git commit -m "<conventional commit describing the fix>"
   git push
   ```

6. **Reply to the comment** — explain fix, deferral, or rejection

7. **Resolve the comment on GitHub**

8. **Delete plan file** if one was created:
   ```bash
   rm .pr-review/plan-<comment-id>.md
   ```

#### 2e. Check stop conditions

Stop iterating if any of:
- No MUST_FIX Copilot comments remain after this pass
- Only OUT_OF_SCOPE Copilot comments remain
- This was the 2nd iteration

Otherwise continue to the next iteration (back to step 2a).

### Step 3 — Summary

Post a final comment on the PR:

```
## Ralph Wiggum Loop — Summary

Completed N Copilot review cycle(s).

### Fixed
- [commit abc1234] <description> (Copilot comment #<id>)
- ...

### Parked
- <description> — deferred, tracked in #<issue>
- ...

### Rejected
- <description> — <reason>
- ...
```

## Resumability

This skill can be interrupted and restarted in a fresh context at any point.

On restart:
1. Run pre-flight (Step 1)
2. Check for an existing `.pr-review/plan-*.md` — if found, continue mid-fix from Step 4b
3. Re-fetch unresolved Copilot comments — already-resolved ones won't appear
4. Continue the outer loop from the current state

## State Directory

`.pr-review/` at the repo root (should be gitignored by the project).
- `plan-<comment-id>.md` — plan for the comment currently in progress (deleted after resolution)
```

**Step 2: Commit**

```bash
git add ralph-wiggum-loop/SKILL.md
git commit -m "feat(ralph-wiggum-loop): add skill definition"
```

---

## Task 3: Write the README files

**Files:**
- Create: `ralph-wiggum-loop/README.md`
- Modify: `README.md` (repo root — add Ralph Wiggum entry)

**Step 1: Write `ralph-wiggum-loop/README.md`**

```markdown
# Ralph Wiggum Loop

An [Agent Skills](https://agentskills.io) skill that automates iterative
GitHub Copilot review loops: trigger Copilot review, address its feedback
one comment at a time, repeat up to 2 cycles.

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
npx skills add xpepper/pr-review-agent-skill/ralph-wiggum-loop -a claude-code
```
```

**Step 2: Update repo-level `README.md`**

Find the `*(coming soon)*` line for Ralph Wiggum Loop and replace it with the real description:

```markdown
### Ralph Wiggum Loop

An automated Copilot-driven review loop: triggers Copilot review, addresses
its feedback one comment at a time, and re-triggers Copilot until all critical
issues are resolved or 2 cycles are complete.

**Install:**
```bash
npx skills add xpepper/pr-review-agent-skill/ralph-wiggum-loop -a claude-code
```

[See skill README →](ralph-wiggum-loop/README.md)
```

**Step 3: Commit**

```bash
git add ralph-wiggum-loop/README.md README.md
git commit -m "docs(ralph-wiggum-loop): add skill README and update repo README"
```

---

## Task 4: Update the packaging script and package the skill

**Files:**
- Modify: `package-skill.sh` (add `ralph-wiggum-loop` to the skills list)

**Step 1: Update `package-skill.sh`**

Find the line:
```bash
SKILLS=("pr-review-loop")
```

Replace with:
```bash
SKILLS=("pr-review-loop" "ralph-wiggum-loop")
```

**Step 2: Run the packaging script**

```bash
./package-skill.sh
```

Expected output:
```
Packaging pr-review-loop...
✓ Created: pr-review-loop.skill (X.XK)
Packaging ralph-wiggum-loop...
✓ Created: ralph-wiggum-loop.skill (X.XK)
```

**Step 3: Verify the package contents**

```bash
unzip -l ralph-wiggum-loop.skill
```

Expected: should list `SKILL.md`, `references/gh-copilot-review-guide.md`, `README.md`.

**Step 4: Commit**

```bash
git add package-skill.sh
git commit -m "build: add ralph-wiggum-loop to packaging script"
```

---

## Task 5: Final verification

**Step 1: Review the full SKILL.md end-to-end**

Read `ralph-wiggum-loop/SKILL.md` carefully. Ask yourself:
- Is every step unambiguous for an agent with no prior context?
- Does the polling/waiting logic clearly describe the timeout behaviour?
- Is the delegation to `pr-review-loop` vs standalone mode clearly explained?
- Does the resumability section correctly describe the restart behaviour?
- Are the stop conditions unambiguous?

Fix any issues found.

**Step 2: Verify repo structure**

```bash
find . -not -path './.git/*' -not -name '.DS_Store' | sort
```

Expected structure:
```
.
├── .gitignore
├── README.md
├── package-skill.sh
├── docs/
│   └── plans/
│       ├── 2026-02-14-pr-review-loop-design.md
│       ├── 2026-02-14-pr-review-loop.md
│       ├── 2026-02-14-ralph-wiggum-loop-design.md
│       └── 2026-02-14-ralph-wiggum-loop.md
├── pr-review-loop/
│   ├── README.md
│   ├── SKILL.md
│   └── references/
│       └── triage-guide.md
└── ralph-wiggum-loop/
    ├── README.md
    ├── SKILL.md
    └── references/
        └── gh-copilot-review-guide.md
```

**Step 3: Commit any final fixes**

```bash
git add -p
git commit -m "fix(ralph-wiggum-loop): address review findings"
```

---

## Done

Both skills are complete. Next steps (out of scope for this plan):
- Publish the repo to GitHub as `xpepper/pr-review-agent-skill`
- Submit both skills to the Agent Skills marketplace
