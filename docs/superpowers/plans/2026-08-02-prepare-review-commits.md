# Prepare Review Commits Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a portable Agent Skill that converts a branch's uncommitted changes into an automatically created, validated, review-friendly sequence of Conventional Commits.

**Architecture:** The implementation is documentation-first: `SKILL.md` is the executable agent workflow and owns all Git safety, inference, commit-boundary, validation, rollback, and reporting rules. Its README explains user installation and invocation; the root catalog positions it as the PR lifecycle's preparation stage. The existing packaging script discovers the new directory without changes.

**Tech Stack:** Agent Skills Markdown and YAML frontmatter; Git; optional `gh`; `npx skills`; Bash.

## Global Constraints

- Deliver a portable Agent Skill named `prepare-review-commits`; do not create client-specific command wrappers.
- Activate only on explicit review-readiness requests, never on vague commit requests.
- Operate on every tracked and untracked, non-ignored uncommitted change; never force-add an ignored path; never rewrite existing commits, fetch, rebase, or push.
- Permit an explicit base branch; otherwise abort if the base cannot be safely inferred.
- Abort before mutating Git state for an unborn branch (no initial commit), detached `HEAD`, in-progress Git operations, conflicts, an untracked embedded Git repository, ambiguous/unrelated work, or unsafe binary/generated-file ownership.
- Treat a clean working tree, or one whose only changes are ignored paths, as a successful no-op — never as an abort or a failure.
- Stage every commit non-interactively; never use `git add -p` or any other command that waits for input.
- Require self-contained vertical commits with their behavior tests; use Conventional Commit types and scopes only where repository convention makes a scope clear.
- Honor hooks and signing; never pass `--no-verify`.
- Run the smallest relevant validation after every commit and the repository's normal full validation after the final commit. If a discovered check fails, restore the exact initial `HEAD`, index, working tree, and untracked files from a backup taken before the first mutation — restoration, not mere drift detection. If no validation command is discoverable, create commits and explicitly report the sequence as unvalidated.
- Do not push. Report base relationship, ordered commits, per-commit files, validation status, and warnings; warn but do not cap a sequence over eight commits.

---

## File Structure

| File | Responsibility |
| --- | --- |
| `prepare-review-commits/SKILL.md` | Defines the portable, automatic Git workflow and its safety constraints. |
| `prepare-review-commits/README.md` | Explains installation, explicit triggers, prerequisites, behavior, and final output. |
| `README.md` | Repositions the catalog as PR preparation and review workflows and links the new skill first. |

### Task 1: Define the Transactional Agent Skill

**Files:**
- Create: `prepare-review-commits/SKILL.md`
- Test: a disposable Git repository outside this repository

**Interfaces:**
- Consumes: the checked-out feature branch, its base branch (explicit or inferred), the complete non-ignored working-tree diff, repository instructions, recent branch history, and optional `gh` PR/issue metadata.
- Produces: a sequence of newly created Conventional Commits from the initial uncommitted diff, or an unchanged repository plus an actionable abort reason.

- [x] **Step 1: Write the skill frontmatter and explicit trigger contract**

Create `prepare-review-commits/SKILL.md` with this frontmatter:

```yaml
---
name: prepare-review-commits
description: Use when explicitly asked to prepare review-ready commits or make an uncommitted branch review-ready before pushing. Organizes only uncommitted changes into validated, self-contained Conventional Commits; never rewrites history or pushes.
license: MIT
compatibility: Requires Git. Optionally uses gh CLI for pull request and issue context.
metadata:
  author: Pietro Di Bello
  version: "1.0.0"
allowed-tools: Bash
---
```

Declare the unrestricted `Bash` capability rather than a `Bash(git:*), Bash(gh:*)`
allowlist. The workflow also needs `mktemp` for its out-of-tree state directory
and must run whatever validation command it discovers in the host repository
(`make`, `npm test`, `pytest`, a project script, …). An allowlist would deny
those commands and make the documented procedure unexecutable.

Immediately state that the workflow must not activate for generic requests such as “commit my changes”; it requires an explicit review-readiness request.

- [x] **Step 2: Specify scope, preflight, intent inference, and no-op behavior**

Add a `## Scope` section stating that the run takes **all** uncommitted,
non-ignored work — tracked modifications and deletions, already-staged index
changes, and untracked non-ignored files — and that it must never include an
ignored path or use `git add -f`.

Then add these ordered sections and exact decision rules:

```markdown
## Preflight

1. Read repository instructions and contributor documentation, then inspect
   the current branch, `HEAD`, status including untracked files, staged and
   unstaged diffs, ignored files, recent history, and the candidate base.
2. Accept an explicit base from the request. Otherwise infer one from the
   branch's tracking configuration, repository default branch, or available
   PR context. Abort if no base can be identified.
3. Abort without changing Git state when the branch has no commit yet
   (unborn `HEAD`), `HEAD` is detached, a merge/rebase/cherry-pick is active,
   or unmerged paths exist. Check the unborn case with
   `git rev-parse --verify --quiet HEAD^{commit}` before any command that
   assumes `HEAD` resolves.
4. Abort if the working tree contains an untracked embedded Git repository,
   whose contents Git can only snapshot as a gitlink.
5. Infer the goal from repository guidance, local history, and optional PR or
   issue context. Abort if the full diff contains unrelated work or the intended
   narrative remains materially ambiguous.
```

Require the skill to report a clean working tree — or one whose only changes
are ignored paths — as a **successful no-op**: not an abort, not a failure.
Require it to inspect the base relationship only; prohibit `git fetch`, `git
rebase`, and all remote mutations.

- [x] **Step 3: Define the commit-planning rules**

Add a `## Plan Commit Boundaries` section that directs the agent to form an
ordered, dependency-respecting sequence of vertical commits. Each commit must:

```markdown
- Explain one reviewable behavior or independently valuable change.
- Include its production code and the tests that establish that behavior.
- Keep pure refactors, documentation, tooling, and formatting separate only
  when each is independently valuable.
- Use `type: imperative subject`; add `(scope)` only where existing repository
  convention makes that scope unambiguous.
- Include generated artifacts and binary files with their unique owning source
  change. Abort if ownership is ambiguous.
```

Require grouping dependent changes rather than emitting a temporarily broken
commit. Prohibit an arbitrary commit count cap and require a warning for more
than eight commits.

- [x] **Step 4: Define exact backup, non-interactive staging, recovery, and verification requirements**

Add a `## Make Changes Transactionally` section built on one premise: any
commit, hook, formatter, code generator, or validation command may mutate the
tree, so recovery must **restore** the exact initial state rather than merely
detect that it drifted.

**Backup, before the first mutation.** Require a state directory created
*outside the repository* (`mktemp -d` in the OS temp directory) — a state
directory inside the worktree pollutes the very `git add -A` snapshot it is
meant to describe. Capture both the index and the full worktree as Git tree
objects, and anchor **each** to its own per-run ref so nothing can
garbage-collect them and a human can recover manually if the agent dies
mid-transaction:

```bash
root="$(git rev-parse --show-toplevel)"
run_id="$(date -u +%Y%m%dT%H%M%SZ)-$$"
state_dir="$(mktemp -d "${TMPDIR:-/tmp}/prepare-review-commits.$run_id.XXXXXX")"
start_head="$(git rev-parse HEAD)"
git status --porcelain=v1 -uall > "$state_dir/status.before"
git ls-files --others --exclude-standard -z > "$state_dir/untracked.before"
index_tree="$(git write-tree)"
rm -f "$state_dir/fp.index"
GIT_INDEX_FILE="$state_dir/fp.index" git -C "$root" read-tree HEAD
GIT_INDEX_FILE="$state_dir/fp.index" git -C "$root" add -A -- .
worktree_tree="$(GIT_INDEX_FILE="$state_dir/fp.index" git write-tree)"
zero=0000000000000000000000000000000000000000
worktree_ref="refs/prepare-review-commits/$run_id/worktree"
index_ref="refs/prepare-review-commits/$run_id/index"
worktree_commit="$(git commit-tree "$worktree_tree" -p "$start_head" \
  -m "prepare-review-commits worktree backup of $start_head")"
index_commit="$(git commit-tree "$index_tree" -p "$start_head" \
  -m "prepare-review-commits index backup of $start_head")"
git update-ref "$worktree_ref" "$worktree_commit" "$zero"
git update-ref "$index_ref" "$index_commit" "$zero"
```

Seeding the fingerprint index from `HEAD` before `git add -A` keeps
tracked-but-ignored files in the snapshot. The zero old-value argument makes
each `update-ref` a create-only operation, so a stale ref left behind by a
crashed earlier run is never overwritten; on collision the agent must pick a
fresh `run_id` or abort, never force or delete another run's ref. Require the
agent to disclose both backup refs and the state directory before the first
change, to delete only its own refs and state directory, and to do so only
after success or after verified recovery.

**Non-interactive staging.** Reset once so the index matches `HEAD`; from then
on `git diff -- <path>` is the whole remaining `HEAD`-to-worktree diff.
Prohibit `git add -p` outright — the workflow runs unattended. Split a file
across commits by writing the selected hunks to a patch file and applying it
to the index only:

```bash
git reset
git add -- <whole-file-paths>          # never `git add -f`
git diff -U3 -- <path> > "$state_dir/candidate.patch"
# Keep the diff header plus only the `@@` hunks owned by this commit; hunk
# line numbers stay valid because every hunk is offset against one pre-image.
git apply --cached --check "$state_dir/commit-<n>.patch"
git apply --cached "$state_dir/commit-<n>.patch"
git commit -m "<conventional message>"
```

Require ordinary `git commit`, with no hook bypass flags. Require the agent to
widen the boundary to whole files or abort **before** starting mutation
whenever a safe precise patch cannot be produced (binary files, a partial
split of a brand-new untracked file, a failing `--check`, any doubt about the
selection); never hand-edit hunk line counts.

**Recovery.** On any staging, hook, commit, or discovered-validation failure,
require all four steps in order. `git reset --hard` is the deliberate,
backup-protected recovery operation authorised here and nowhere else:

```bash
git reset --hard "$start_head"
git clean -fd          # never -x or -ff: ignored content is left untouched
git read-tree --reset -u "$worktree_tree"
git read-tree "$index_tree"
git update-index -q --refresh || true
```

`git clean -fd` removes transaction-created untracked content *and* the
originals. `git read-tree --reset -u "$worktree_tree"` then forces the
working tree to the snapshot: it rewrites drifted content **and removes paths
the snapshot does not contain**, which is what restores in-scope deletions.
`checkout-index` must not be used here — it only writes files present in the
tree and never removes any, so `git reset --hard` would resurrect every
tracked file that was deleted before the run and recovery would merely detect
the mismatch. `git read-tree "$index_tree"` finally restores the
staged/unstaged split without touching worktree content.

**Verification.** Require four checks — `HEAD`, the index tree, a freshly
recomputed worktree tree, and a `status --porcelain=v1 -uall` diff — to all
pass before any success claim, and require both backup refs and the state
directory to be retained with the mismatch reported if any check fails.
Require guarded cleanup (`git update-ref -d <ref> <expected-oid>`) so no run
can delete another run's backup, and document the manual replay path
(`<ref>^` is the run's starting commit). Require the skill to state its honest
limits: ignored content is deliberately not reverted; a pre-existing empty
directory is removed by `git clean -fd` and not restored; and a Git repository
created inside the worktree during the run cannot be cleaned safely, so the
skill must fail loudly rather than claim exact restoration.

- [x] **Step 5: Define validation and completion reporting**

Add `## Validate Each Commit` and `## Report` sections that require:

```markdown
1. Discover repository validation commands from instructions, scripts,
   Makefiles, and CI configuration; never invent a command.
2. Run the smallest relevant discovered command after each commit.
3. Run the normal full discovered validation after the final commit.
4. On any discovered-command failure, run transactional recovery and report
   the failing command and output.
5. If no validation command exists, proceed but mark every created commit and
   the final summary as unvalidated.
```

Require the final report to include the inferred/explicit base and its local
relationship, the ordered commit list with message and changed files, targeted
and final validation results, warnings (including long sequence and
unvalidated state), and an explicit statement that nothing was pushed. If the
run ended in recovery, require it to report whether recovery verification
passed and, if not, the retained backup ref and state directory.

- [x] **Step 6: Run a manual happy-path verification**

Run the workflow in a disposable repository containing a small application
change and its test. Request an explicit base branch, verify that it produces
vertical Conventional Commits, inspect `git log --reverse --oneline
<base>..HEAD`, and confirm that no remote command is attempted.

- [x] **Step 7: Run non-interactive staging, recovery, and safety verification**

In disposable repositories outside this repository, exercise each scenario
non-interactively:

*Hunk-level split without `git add -p`* — one file carrying two unrelated
changes plus an untracked test file, split across two commits:

```bash
git reset
git diff -U3 -- app.txt > candidate.patch   # select only the owned @@ hunks
git apply --cached --check commit1.patch && git apply --cached commit1.patch
git add -- app_test.txt && git commit -m "feat: ..."
git diff        # must show only the remaining hunk
```

*Hostile mutation plus failure* — a discovered validation command that appends
to a tracked file, writes a new untracked file, deletes an untracked original,
recreates a file the run had deleted, and exits non-zero; and a `pre-commit`
hook that reformats a tracked file and generates an untracked file. Build the
starting state so it contains a staged deletion (`D `), an unstaged deletion
(` D`), a deletion that empties a directory, a staged addition further
modified in the worktree (`AM`), a mixed staged/unstaged edit (`MM`),
untracked originals, and an ignored artifact. After recovery, all four checks
must pass:

```bash
test "$(git rev-parse HEAD)" = "$start_head"
test "$(git write-tree)" = "$index_tree"
# recomputed worktree tree must equal $worktree_tree
diff status.before <(git status --porcelain=v1 -uall)
```

Also confirm that every deleted path is absent again after recovery, that an
ignored artifact survives recovery untouched, that a create-only
`git update-ref` refuses to overwrite a stale backup ref, and that an unborn
branch, an unresolved conflict, and an unknown base each abort before any
mutation with `HEAD` unchanged.

- [x] **Step 8: Commit**

```bash
git add prepare-review-commits/SKILL.md
git commit -m "feat(prepare-review-commits): add transactional commit workflow"
```

### Task 2: Document Installation and User Contract

**Files:**
- Create: `prepare-review-commits/README.md`
- Test: rendered Markdown review and a package installation smoke test

**Interfaces:**
- Consumes: the workflow contract in `prepare-review-commits/SKILL.md`.
- Produces: concise cross-agent installation and invocation guidance without duplicating implementation details.

- [x] **Step 1: Write the README introduction and installation command**

Create `prepare-review-commits/README.md` with:

````markdown
# Prepare Review Commits

An [Agent Skills](https://agentskills.io) skill that turns the current
uncommitted diff into a logical sequence of conventional commits, ready for
pull-request review.

## Install

```bash
npx skills add xpepper/pr-review-agent-skill/prepare-review-commits
```
````

- [x] **Step 2: Document explicit activation and key behavior**

Add examples that activate the skill:

```text
Prepare review-ready commits for this branch
Make this branch review-ready before I push
Use prepare-review-commits against release/2.4
```

State that it does not run for generic commit requests. Describe that it
includes all tracked and untracked non-ignored changes, handles conventional
commit messages, keeps tests with behavior, validates commits when commands
are discoverable, restores state on failure, and never pushes, rebases, fetches,
or rewrites existing commits.

- [x] **Step 3: Document prerequisites and final report**

List Git as required and `gh` as optional. Explain that an explicit base branch
can be supplied and that missing base context, conflicts, an active Git
operation, or ambiguous unrelated work cause a no-change abort. Show the final
report fields: base relationship, ordered commits and files, validation status,
warnings, and no-push confirmation.

- [x] **Step 4: Review the README against the skill contract**

Check every claim against `prepare-review-commits/SKILL.md`. Remove wording
that implies a client-specific command, automatic push, history rewrite, or
validation when no repository command was available.

- [x] **Step 5: Commit**

```bash
git add prepare-review-commits/README.md
git commit -m "docs(prepare-review-commits): add installation guide"
```

### Task 3: Add the Skill to the Lifecycle Catalog and Verify Packaging

**Files:**
- Modify: `README.md`
- Generated: `prepare-review-commits.skill` (ignored build artifact)

**Interfaces:**
- Consumes: `prepare-review-commits/SKILL.md` and `prepare-review-commits/README.md`.
- Produces: a discoverable lifecycle catalog entry and an installable skill package.

- [x] **Step 1: Reposition the catalog**

Change the root title description from:

```markdown
# PR Review Agent Skills

A collection of [Agent Skills](https://agentskills.io) for automating PR code review workflows.
```

to:

```markdown
# PR Preparation and Review Agent Skills

A collection of [Agent Skills](https://agentskills.io) for preparing changes and
automating pull-request review workflows.
```

Insert `### Prepare Review Commits` as the first skill entry, with a short
description, its `npx skills add` command, and a relative README link matching
the existing catalog format.

- [x] **Step 2: Build all skill packages**

Run:

```bash
./package-skill.sh
```

Expected: the output lists `prepare-review-commits` and creates
`prepare-review-commits.skill`. Do not stage the generated package because
`*.skill` is an ignored build artifact.

- [ ] **Step 3: Test project-local installation and removal** — DEFERRED, not
  yet done

Run:

```bash
npx skills add xpepper/pr-review-agent-skill/prepare-review-commits -a claude-code --yes
npx skills remove prepare-review-commits -a claude-code --yes
```

Expected: installation exposes the `prepare-review-commits` description under
`.agents/skills/prepare-review-commits`, and removal succeeds. Remove any
temporary project-local installation residue if the installer leaves it behind.

**Deferred:** this step is intentionally left unchecked and outstanding.
`npx skills add` resolves the skill from GitHub, so it cannot run until
`feat/prepare-review-commits` is pushed. Run it once, unchanged, immediately
after the first push, tick the box only then, and treat a failure there as a
follow-up fix rather than a plan change.

- [x] **Step 4: Inspect the final change set**

Run:

```bash
git diff --check main...HEAD
git status --short
git log --reverse --oneline main..HEAD
```

Expected: only the skill, its README, the root catalog update, and the
previously committed design/plan documentation are tracked; generated packages
and unrelated local files remain unstaged.

- [x] **Step 5: Commit**

```bash
git add README.md
git commit -m "docs: add prepare-review-commits to lifecycle catalog"
```

## Plan Self-Review

**Spec coverage:** Task 1 covers the portable, explicitly triggered,
uncommitted-only, base-aware, transactional workflow; its scope, boundary,
message, generated/binary, non-interactive staging, validation, backup,
restore-and-verify recovery, and no-push rules. Task 2 covers cross-agent
installation and user expectations. Task 3 covers the approved catalog
positioning, automatic packaging, and installation verification.

**Placeholder scan:** The plan names all files, commands, required report
fields, and safety behavior. The only deferred item is Task 3 Step 3, which
depends on the branch being pushed to GitHub and therefore stays unchecked
until that push happens.

**Consistency check:** The README and catalog both name
`prepare-review-commits`; the package command matches the directory; all
validation and recovery behavior originates in the single workflow definition.
The frontmatter declares the unrestricted `Bash` capability, which is what the
documented `mktemp` and discovered-validation commands actually require.
