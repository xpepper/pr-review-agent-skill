# PR Review Loop — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create the `pr-review-loop` agent skill in a new `pr-review-agent-skill` repo that automates addressing PR review comments one at a time with a resumable, opinionated workflow.

**Architecture:** A single `SKILL.md` file drives the agent's behaviour via natural language instructions. Supporting reference documents (triage guide, etc.) are bundled alongside. The skill is packaged as a `.skill` zip file for distribution via the Agent Skills CLI.

**Tech Stack:** `gh` CLI (preferred) or GitHub REST API, git, bash, Agent Skills standard (SKILL.md + references/)

---

## Task 1: Create and initialise the new repo

**Files:**
- Create: `~/Documents/workspace/ai/pr-review-agent-skill/` (new repo root)

**Step 1: Create the repo directory and initialise git**

```bash
mkdir -p ~/Documents/workspace/ai/pr-review-agent-skill
cd ~/Documents/workspace/ai/pr-review-agent-skill
git init
```

Expected: `Initialized empty Git repository in .../pr-review-agent-skill/.git/`

**Step 2: Create a .gitignore**

```bash
cat > .gitignore << 'EOF'
.DS_Store
*.skill
marketing/
playground/
EOF
```

Note: `.skill` files are build artefacts, not committed.

**Step 3: Create the initial directory structure**

```bash
mkdir -p pr-review-loop/references
mkdir -p docs/plans
```

**Step 4: Copy the design document into the new repo**

Copy `docs/plans/2026-02-14-pr-review-loop-design.md` from `perplexity-agent-skill` into `docs/plans/` of the new repo.

**Step 5: Commit initial structure**

```bash
git add .gitignore docs/
git commit -m "chore: initialise repo with structure and design doc"
```

---

## Task 2: Write the triage reference guide

**Files:**
- Create: `pr-review-loop/references/triage-guide.md`

This document is bundled with the skill and referenced by the agent at runtime.

**Step 1: Write the triage guide**

```markdown
# Triage Guide

When classifying PR review comments, assign one of four categories:

## MUST_FIX
A blocking issue that must be resolved before the PR can merge.

Indicators:
- Reviewer explicitly says "blocking", "must fix", "required"
- Correctness bug or security issue
- Breaks tests or build
- Violates project conventions that are explicitly documented

## SHOULD_FIX
Non-blocking but worth addressing in this PR to improve quality.

Indicators:
- Reviewer says "nit", "suggestion", "consider", "ideally"
- Style or readability improvement
- Clear improvement with low risk and small effort
- Would reduce future confusion or maintenance burden

## PARK
Valid concern, but intentionally deferred outside this PR.

Use when:
- The fix requires changes in a different PR or component
- The effort is disproportionate to the PR scope
- It's a known existing issue not introduced by this PR
- You are deferring: create a follow-up issue and reference it in your reply

## OUT_OF_SCOPE
Not applicable to this PR; rejected with explanation.

Use when:
- Comment is based on a misunderstanding
- The suggested approach contradicts project conventions
- The comment refers to code not changed by this PR
- A prior discussion or decision already covers this

---

## Triage Tips

- When in doubt between MUST_FIX and SHOULD_FIX, ask: "Would a reviewer block merge over this?" If yes, MUST_FIX.
- When in doubt between SHOULD_FIX and PARK, ask: "Can this be done safely within this PR's scope?" If yes, SHOULD_FIX.
- If you need external knowledge (e.g., is this pattern idiomatic in this language/framework?), use Perplexity if available.
- Triage all comments before acting on any. This gives you a full picture before committing to changes.
```

**Step 2: Commit**

```bash
git add pr-review-loop/references/triage-guide.md
git commit -m "docs(pr-review-loop): add triage guide reference"
```

---

## Task 3: Write the SKILL.md

**Files:**
- Create: `pr-review-loop/SKILL.md`

This is the main skill file. It must be complete and self-contained — the agent reads it at runtime and follows it literally.

**Step 1: Write SKILL.md**

```markdown
# PR Review Loop

## Purpose

Address all open PR review comments one at a time using an opinionated, resumable workflow. Works with comments from any reviewer (human or bot).

## Prerequisites

- `gh` CLI (preferred). If unavailable, fall back to the GitHub REST API.
- The PR branch must be checked out locally.

## Process

### Step 1 — Pre-flight

Inspect the project for safeguard conventions by checking these files (if they exist):
- `CLAUDE.md`, `AGENTS.md`
- `Makefile`
- `.github/workflows/`
- `README.md`

Identify all required safeguards (tests, compilation, linting, formatting, etc.).
Run all of them. If any fail, stop immediately and report — do not proceed on a broken baseline.

### Step 2 — Collect

Fetch all unresolved PR comments.

Preferred (gh CLI):
```bash
gh pr view --json comments,reviews
gh api repos/{owner}/{repo}/pulls/{pr}/comments
```

Fallback (REST API):
```bash
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/{owner}/{repo}/pulls/{pr}/comments
```

Filter to only unresolved comments.

### Step 3 — Triage

Read `references/triage-guide.md`.

Classify every unresolved comment as: MUST_FIX, SHOULD_FIX, PARK, or OUT_OF_SCOPE.

Triage all comments before acting on any.

If Perplexity is available and a comment requires external knowledge to classify (e.g., library idioms, language conventions), use it:
```bash
llm -m sonar 'your question here'
```

### Step 4 — Process one comment at a time

Process in order: all MUST_FIX first, then SHOULD_FIX.
Skip PARK and OUT_OF_SCOPE for now (they are handled in the summary).

For each comment:

**4a. Assess complexity**

Is this trivial (e.g., rename a function, fix a typo, adjust formatting)?
- Yes → fix directly, no plan needed
- No → create a plan file at `.pr-review/plan-<comment-id>.md` before touching any code

The plan file must describe:
- What the comment is asking for
- The approach to fix it
- Files that will be changed

**4b. Run safeguards**

Run all safeguards identified in Step 1. They must all pass before you touch any code.
If they fail, stop and report.

**4c. Fix or park**

- Fix: implement the change
- Park (if you discover mid-fix that it should be parked): write reasoning, revert any partial changes, no commit

**4d. Run safeguards again**

Run all safeguards. They must all pass.
If they fail, fix the regression before moving on — do not skip this step.

**4e. Commit and push**

```bash
git add <changed files>
git commit -m "<conventional commit message describing the fix>"
git push
```

**4f. Reply to the PR comment**

Post a reply on the PR comment explaining:
- What was done (for fixes: reference the commit)
- Why it was parked (for deferred items)
- Why it was rejected (for out-of-scope items)

Preferred (gh CLI):
```bash
gh api repos/{owner}/{repo}/pulls/comments/{comment_id}/replies \
  -f body="<reply text>"
```

**4g. Resolve the comment**

Mark the comment as resolved on GitHub.

```bash
gh api repos/{owner}/{repo}/pulls/comments/{comment_id} \
  --method PATCH -f resolved=true
```

**4h. Delete plan file**

If a plan file was created, delete it:
```bash
rm .pr-review/plan-<comment-id>.md
```

### Step 5 — Stop condition

Stop when no MUST_FIX or SHOULD_FIX comments remain.

### Step 6 — Summary

Post a final comment on the PR summarising:

```
## PR Review Loop — Summary

### Fixed
- [commit abc1234] Renamed `foo` to `bar` (comment by @alice)
- ...

### Parked
- Refactor of X module deferred — tracked in #<issue> (comment by @bob)
- ...

### Rejected
- Suggestion to use Y rejected: project convention is Z (comment by @carol)
- ...
```

## Resumability

This skill is designed to be interrupted and restarted in a fresh context at any point.

On startup:
1. Run pre-flight (Step 1)
2. Re-fetch unresolved comments from GitHub (Step 2) — already-resolved comments won't appear
3. Check for an existing `.pr-review/plan-*.md` file — if found, you are mid-fix on that comment; continue from Step 4b
4. Triage remaining comments and continue

This means no progress is ever lost. Each fix is committed and pushed before moving on.

## State Directory

`.pr-review/` at the repo root (gitignored by the project).
- `plan-<comment-id>.md` — plan for the comment currently in progress (deleted after resolution)
```

**Step 2: Commit**

```bash
git add pr-review-loop/SKILL.md
git commit -m "feat(pr-review-loop): add skill definition"
```

---

## Task 4: Write the README

**Files:**
- Create: `README.md` (repo-level)

**Step 1: Write README.md**

```markdown
# PR Review Agent Skills

A collection of [Agent Skills](https://agentskills.io) for automating PR code review workflows.
Compatible with Claude Code, GitHub Copilot, Cursor, Windsurf, and 30+ other agents.

## Skills

### PR Review Loop

Addresses all open PR review comments one at a time using an opinionated, resumable workflow.
Works with any reviewer (human or bot).

**Install:**
```bash
npx skills add xpepper/pr-review-agent-skill/pr-review-loop -a claude-code
```

[See skill README →](pr-review-loop/README.md)

---

### Ralph Wiggum Loop *(coming soon)*

An automated Copilot review loop: triggers Copilot review, addresses feedback, and repeats
until all critical issues are resolved.

---

## Requirements

- `gh` CLI (recommended) or a GitHub token for REST API fallback
- Git

## License

MIT
```

**Step 2: Write `pr-review-loop/README.md`**

```markdown
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
```

**Step 3: Commit**

```bash
git add README.md pr-review-loop/README.md
git commit -m "docs: add repo and skill READMEs"
```

---

## Task 5: Write the packaging script and package the skill

**Files:**
- Create: `package-skill.sh`

**Step 1: Write package-skill.sh**

```bash
#!/bin/bash
# Package agent skills into .skill files

set -e

SKILLS=("pr-review-loop")

for SKILL in "${SKILLS[@]}"; do
  SKILL_FILE="${SKILL}.skill"

  if [ ! -d "$SKILL" ]; then
    echo "Error: Skill directory '$SKILL' not found"
    exit 1
  fi

  if [ ! -f "$SKILL/SKILL.md" ]; then
    echo "Error: SKILL.md not found in '$SKILL'"
    exit 1
  fi

  echo "Packaging $SKILL..."
  cd "$SKILL"
  zip -r "../${SKILL_FILE}" . -x "*.DS_Store" -x "__pycache__/*" -x "*.pyc"
  cd ..

  SIZE=$(ls -lh "${SKILL_FILE}" | awk '{print $5}')
  echo "✓ Created: ${SKILL_FILE} ($SIZE)"
done
```

**Step 2: Make it executable**

```bash
chmod +x package-skill.sh
```

**Step 3: Run the packaging script**

```bash
./package-skill.sh
```

Expected output:
```
Packaging pr-review-loop...
✓ Created: pr-review-loop.skill (X.XK)
```

**Step 4: Verify the package contents**

```bash
unzip -l pr-review-loop.skill
```

Expected: should list `SKILL.md`, `references/triage-guide.md`, `README.md`.

**Step 5: Commit**

```bash
git add package-skill.sh
git commit -m "build: add packaging script"
```

Note: the `.skill` file itself is not committed (it's in `.gitignore`).

---

## Task 6: Final verification

**Step 1: Review the full SKILL.md end-to-end**

Read `pr-review-loop/SKILL.md` carefully. Ask yourself:
- Is every step unambiguous for an agent with no prior context?
- Are all `gh` CLI commands syntactically correct?
- Does the resumability section correctly describe the restart behaviour?
- Are triage categories clearly defined in the reference guide?

Fix any issues found.

**Step 2: Verify repo structure**

```bash
find . -not -path './.git/*' -not -name '.DS_Store'
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
│       └── 2026-02-14-pr-review-loop.md
└── pr-review-loop/
    ├── README.md
    ├── SKILL.md
    └── references/
        └── triage-guide.md
```

**Step 3: Commit any final fixes**

```bash
git add -p
git commit -m "fix(pr-review-loop): address review findings"
```

---

## Done

The skill is ready. Next steps (out of scope for this plan):
- Publish to GitHub as `xpepper/pr-review-agent-skill`
- Submit to the Agent Skills marketplace
- Design Skill 2: Ralph Wiggum Loop (see design doc for context)
