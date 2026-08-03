---
name: prepare-review-commits
description: Use when explicitly asked to prepare review-ready commits or make an uncommitted branch review-ready before pushing. Organizes only uncommitted changes into validated, self-contained Conventional Commits; never rewrites history or pushes.
license: MIT
compatibility: Requires Git. Optionally uses gh CLI for pull request and issue context.
metadata:
  author: Pietro Di Bello
  version: "1.1.0"
allowed-tools: Bash
disable-model-invocation: true
---

# Prepare Review Commits

## Trigger

This skill is **manual-only** (`disable-model-invocation: true`): an agent must
never load or run it on its own initiative. It runs only when a human invokes
it explicitly — `/prepare-review-commits`, or a request that names the skill.

Even once invoked, the request must be a review-readiness one — for example
"prepare review-ready commits" or "make this branch review-ready before I
push". Generic requests such as "commit my changes" are out of scope; say so
and stop rather than proceeding.

## Scope

Take **all** uncommitted, non-ignored work on the branch into the sequence:
tracked modifications and deletions, changes already staged in the index, and
untracked files that Git does not ignore. Nothing in that set may be silently
left behind — if part of it cannot be committed safely, abort and say why.

Never include an ignored path, and never use `git add -f` / `git add --force`
to pull one in. If an ignored file looks like it belongs to the change, report
it and let the user decide.

## Preflight

1. Read repository instructions and contributor documentation, then inspect
   the current branch, `HEAD`, status including untracked files, staged and
   unstaged diffs, ignored files, recent history, and the candidate base.
2. Accept an explicit base from the request. Otherwise infer one from the
   branch's tracking configuration, repository default branch, or available
   PR context. Abort if no base can be identified.
3. Abort without changing Git state when the branch has no commit yet (unborn
   `HEAD`), `HEAD` is detached, a merge/rebase/cherry-pick is active, or
   unmerged paths exist. Check the unborn case with
   `git rev-parse --verify --quiet HEAD^{commit}` **before** running any
   command that assumes `HEAD` resolves — plain `git rev-parse HEAD` fails on
   an unborn branch.
4. Abort if the working tree contains an untracked embedded Git repository.
   Git snapshots such a directory only as a gitlink, so the backup below
   cannot restore its contents and the transaction cannot be made safe.
5. Infer the goal from repository guidance, local history, and optional PR or
   issue context. Abort if the full diff contains unrelated work or the intended
   narrative remains materially ambiguous.

A clean working tree — or one whose only changes are ignored paths — is a
**successful no-op**, not an abort and not a failure. Report that there was
nothing to commit, leave Git untouched, and stop.

Inspect the base relationship only. Never run `git fetch`, `git rebase`, or
any command that mutates a remote.

## Plan Commit Boundaries

Form an ordered, dependency-respecting sequence of vertical commits. Each
commit must:

- Explain one reviewable behavior or independently valuable change.
- Include its production code and the tests that establish that behavior.
- Keep pure refactors, documentation, tooling, and formatting separate only
  when each is independently valuable.
- Use `type: imperative subject`; add `(scope)` only where existing repository
  convention makes that scope unambiguous.
- Include generated artifacts and binary files with their unique owning source
  change. Abort if ownership is ambiguous.

Group dependent changes together rather than emitting a temporarily broken
commit. Never cap the number of commits at an arbitrary limit, but warn the
user when the plan produces more than eight commits.

## Make Changes Transactionally

Every commit, hook, formatter, code generator, and validation command may
mutate the working tree. Treat the whole sequence as one transaction: take a
complete backup **before** the first mutation, and on any failure restore the
exact initial tracked, staged, unstaged, and untracked state — do not merely
detect that it drifted.

### 1. Take the backup

Create the state directory **outside the repository** (in the OS temp
directory) so no recovery step can reach it and it never appears in
`git status`:

```bash
root="$(git rev-parse --show-toplevel)"
run_id="$(date -u +%Y%m%dT%H%M%SZ)-$$"
state_dir="$(mktemp -d "${TMPDIR:-/tmp}/prepare-review-commits.$run_id.XXXXXX")"

start_head="$(git rev-parse HEAD)"
git status --porcelain=v1 -uall > "$state_dir/status.before"
# The untracked, non-ignored files this run adopts (used by the final report).
git ls-files --others --exclude-standard -z > "$state_dir/untracked.before"

# Exact staged (index) state.
index_tree="$(git write-tree)"

# Exact worktree state — tracked plus non-ignored untracked — as one tree.
rm -f "$state_dir/fp.index"
GIT_INDEX_FILE="$state_dir/fp.index" git -C "$root" read-tree HEAD
GIT_INDEX_FILE="$state_dir/fp.index" git -C "$root" add -A -- .
worktree_tree="$(GIT_INDEX_FILE="$state_dir/fp.index" git write-tree)"

# Anchor BOTH snapshots to per-run refs so neither can be garbage-collected
# and a human can recover manually if this agent dies mid-transaction.
zero=0000000000000000000000000000000000000000
worktree_ref="refs/prepare-review-commits/$run_id/worktree"
index_ref="refs/prepare-review-commits/$run_id/index"
worktree_commit="$(git commit-tree "$worktree_tree" -p "$start_head" \
  -m "prepare-review-commits worktree backup of $start_head")"
index_commit="$(git commit-tree "$index_tree" -p "$start_head" \
  -m "prepare-review-commits index backup of $start_head")"
# The trailing zero OID is an "old value" precondition: the update succeeds
# only if the ref does not exist yet, so a stale ref left by a crashed run is
# never overwritten.
git update-ref "$worktree_ref" "$worktree_commit" "$zero"
git update-ref "$index_ref" "$index_commit" "$zero"
printf 'run_id=%s\nstart_head=%s\nindex_tree=%s\nworktree_tree=%s\nworktree_ref=%s\nworktree_commit=%s\nindex_ref=%s\nindex_commit=%s\n' \
  "$run_id" "$start_head" "$index_tree" "$worktree_tree" \
  "$worktree_ref" "$worktree_commit" "$index_ref" "$index_commit" \
  > "$state_dir/refs.before"
```

`GIT_INDEX_FILE` keeps this snapshot out of the real index, and seeding it
from `HEAD` first means tracked-but-ignored files are captured too.

Both backups are durable and per-run: the refs live under
`refs/prepare-review-commits/<run_id>/`, and `mktemp -d` gives this run its
own state directory. Nothing this run writes can clobber another run's
backup. If either `git update-ref` fails because the ref already exists, do
**not** delete or force it — that ref belongs to a different (possibly
crashed) run. Pick a fresh `run_id` and retry; if it still collides, abort
before mutating anything.

Tell the user both backup refs and the state directory path before the first
change.

### 2. Stage each planned commit non-interactively

Reset once so the index matches `HEAD`; from then on `git diff -- <path>` is
the whole remaining `HEAD`-to-worktree diff for that path.

```bash
git reset
```

Stage whole files directly:

```bash
git add -- <path>...   # never `git add -f`
```

When one file's changes belong to more than one commit, do **not** use the
interactive `git add -p` — this workflow must run unattended. Write the
selected hunks to a patch file and apply that patch to the index:

```bash
git diff -U3 -- <path> > "$state_dir/candidate.patch"
# Copy the `diff --git` / `index` / `---` / `+++` header plus only the `@@`
# hunks that belong to this commit into "$state_dir/commit-<n>.patch". Hunk
# line numbers stay valid because every hunk is offset against the same
# pre-image, so a subset of hunks applies unchanged.
git apply --cached --check "$state_dir/commit-<n>.patch"   # dry run first
git apply --cached "$state_dir/commit-<n>.patch"
```

`git apply --cached` touches only the index, so the working tree keeps the
remaining changes for later commits. Confirm the staged result with
`git diff --cached` before committing, and regenerate the diff after each
commit instead of reusing a stale patch.

If a precise patch cannot be produced safely — a binary file, a partial split
of a brand-new untracked file, a failing `--check`, or any uncertainty about
the selection — widen that boundary to whole files, or abort **before**
starting mutation. Never hand-edit hunk line counts or guess offsets.

Commit with ordinary `git commit`. Never pass hook-bypass flags (e.g.
`--no-verify`) — honor hooks and commit signing as configured:

```bash
git commit -m "<conventional message>"
```

### 3. Recover on any failure

Run recovery when staging, a hook, a commit, or a discovered validation
command fails. Execute every step in order from the repository root. This is
the only place a destructive Git command is permitted, and only because the
backup above is complete and lives outside the working tree.

```bash
# a. Drop the transaction commits and move HEAD and the index back to the
#    starting commit (backup-protected).
git reset --hard "$start_head"

# b. Delete every non-ignored untracked path, including the ones the
#    transaction created. Step c restores the originals from the backup.
#    `git clean -fd` (never `-x`, never `-ff`) leaves ignored content and
#    nested Git repositories untouched.
git clean -fd

# c. Force the working tree back to the snapshot. `read-tree --reset -u`
#    both rewrites files whose content drifted AND removes files that the
#    snapshot does not contain — which is what restores the in-scope
#    deletions that step (a) just undid. `checkout-index` cannot do this:
#    it only writes files present in the tree and never removes any, so a
#    tracked file deleted before the run would silently come back.
git read-tree --reset -u "$worktree_tree"

# d. Restore the exact staged/unstaged split. This rewrites the index only;
#    the working tree content settled in step (c) is left alone, so the
#    files this run adopted as untracked become untracked again.
git read-tree "$index_tree"
git update-index -q --refresh || true
```

Why this order matters: step (a) resurrects every tracked file that was
deleted in the starting state, and step (b) cannot remove them because they
are tracked again. Only step (c) — a tree-driven update that deletes as well
as writes — brings staged deletions (`D `), unstaged deletions (` D`), and
deletions that empty a directory back to their pre-run state.

Ignored content survives all four steps: `git clean -fd` skips ignored paths,
and `read-tree --reset -u` only touches paths that are in the old index or in
the target tree.

### 4. Verify the recovery, then clean up

Recovery is not finished until all four checks pass:

```bash
test "$(git rev-parse HEAD)" = "$start_head"
test "$(git write-tree)" = "$index_tree"

rm -f "$state_dir/verify.index"
GIT_INDEX_FILE="$state_dir/verify.index" git -C "$root" read-tree HEAD
GIT_INDEX_FILE="$state_dir/verify.index" git -C "$root" add -A -- .
test "$(GIT_INDEX_FILE="$state_dir/verify.index" git write-tree)" = "$worktree_tree"

git status --porcelain=v1 -uall > "$state_dir/status.after"
diff "$state_dir/status.before" "$state_dir/status.after"
```

Only after all four pass — or after the full sequence succeeds with no
recovery — remove this run's backup. Delete each ref with its expected old
value so a concurrent or later run's ref can never be removed by mistake, and
remove only this run's state directory:

```bash
git update-ref -d "$worktree_ref" "$worktree_commit"
git update-ref -d "$index_ref" "$index_commit"
rm -rf "$state_dir"
```

Never delete a ref under `refs/prepare-review-commits/` that this run did not
create, and never run a bulk cleanup of that namespace: a surviving ref means
some run did not finish, and only its owner can say whether it is still
needed.

If any check fails, stop immediately, change nothing else, keep both backup
refs and `$state_dir`, and report the exact mismatch together with the manual
recovery handles. A human can list every retained backup and replay the
recovery for one run like this:

```bash
# List retained backups from crashed or failed runs, newest last.
git for-each-ref --sort=creatordate \
  --format='%(refname) %(objectname:short) %(creatordate:iso)' \
  refs/prepare-review-commits/

# Replay recovery for one run. Both backup commits are parented on the run's
# starting commit, so `<ref>^` is that commit.
run=refs/prepare-review-commits/<run_id>
git reset --hard "$run/worktree^"
git clean -fd
git read-tree --reset -u "$run/worktree^{tree}"
git read-tree "$run/index^{tree}"
git update-index -q --refresh || true

# Then drop that run's backup.
git update-ref -d "$run/worktree"
git update-ref -d "$run/index"
```

To inspect a snapshot without touching the working tree, use
`git show --stat <run>/worktree` or
`git checkout <run>/worktree -- <path>` for a single file — but note that
`git checkout <ref> -- .` restores files without removing extra ones, so it
is a partial handle, not the full recovery above.

Never claim recovery succeeded without those checks passing.

State these limits rather than papering over them:

- **Ignored content is deliberately left alone.** An ignored artifact written,
  changed, or deleted by a hook or validation command is not reverted. This
  does not weaken the guarantee for in-scope work: every non-ignored tracked
  and untracked path is restored exactly, including deletions.
- **Empty directories are not tracked by Git.** A directory that was empty
  before the run — and any directory left empty because the run's only content
  under it was untracked — is removed by step (b) and not recreated. No file
  content is lost.
- **A Git repository created inside the working tree during the run cannot be
  cleaned safely.** `git clean -fd` will not descend into a directory holding
  its own `.git`, and `-ff` is forbidden here because it deletes repositories
  outright. If a hook, code generator, or validation command creates one, the
  worktree-tree and status checks above will fail. Do not retry with `-ff` and
  do not claim exact restoration: stop, keep both backup refs and the state
  directory, name the leftover repository path, and let the user remove it.

## Validate Each Commit

1. Discover repository validation commands from instructions, scripts,
   Makefiles, and CI configuration; never invent a command.
2. Run the smallest relevant discovered command after each commit.
3. Run the normal full discovered validation after the final commit.
4. On any discovered-command failure, run the transactional recovery in
   "Make Changes Transactionally" — including its verification — and report
   the failing command and its output.
5. If no validation command exists, proceed but mark every created commit and
   the final summary as unvalidated.

## Report

The final report must include:

- The inferred or explicit base and its local relationship to the branch.
- The ordered commit list, each with its message and changed files.
- Targeted and final validation results (or the unvalidated warning).
- Warnings, including a long commit sequence (more than eight) and an
  unvalidated state.
- An explicit statement that nothing was pushed.

If the run ended in recovery, also report whether recovery verification
passed. If it did not, report the mismatch, the retained backup refs
`refs/prepare-review-commits/<run_id>/worktree` and
`refs/prepare-review-commits/<run_id>/index`, and the retained state
directory path.

## Do Not

- Activate for a generic "commit my changes" request without explicit
  review-readiness intent.
- Rewrite, amend, or reorder any commit that existed before this workflow ran.
- Run `git fetch`, `git rebase`, `git push`, or any other remote mutation.
- Bypass hooks or commit signing.
- Use interactive commands such as `git add -p`, `git rebase -i`, or anything
  that opens an editor or waits for keyboard input.
- Force-add ignored paths, or run any `git clean` variant with `-x` or `-ff`.
- Run `git reset --hard`, `git clean`, or any other destructive command
  outside the documented, backup-protected recovery procedure.
- Delete, overwrite, or bulk-clean a `refs/prepare-review-commits/` ref that
  the current run did not create.
- Cap the commit count at an arbitrary number.
- Claim recovery succeeded without passing every recovery verification check.
- Treat a clean or ignored-only working tree as a failure.
