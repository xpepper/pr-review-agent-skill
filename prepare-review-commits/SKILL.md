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

# Prepare Review Commits

## Trigger

This workflow activates only for an explicit review-readiness request — for
example "prepare review-ready commits" or "make this branch review-ready
before I push". It must **not** activate for generic requests such as "commit
my changes"; those are out of scope for this skill.

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
state_dir="$(mktemp -d "${TMPDIR:-/tmp}/prepare-review-commits.XXXXXX")"

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

# Anchor the snapshot to a ref so it cannot be garbage-collected and a human
# can recover manually if this agent dies mid-transaction.
backup_commit="$(git commit-tree "$worktree_tree" -p "$start_head" \
  -m "prepare-review-commits backup of $start_head")"
git update-ref refs/prepare-review-commits/backup "$backup_commit"
printf 'start_head=%s\nindex_tree=%s\nworktree_tree=%s\nbackup=%s\n' \
  "$start_head" "$index_tree" "$worktree_tree" "$backup_commit" \
  > "$state_dir/refs.before"
```

`GIT_INDEX_FILE` keeps this snapshot out of the real index, and seeding it
from `HEAD` first means tracked-but-ignored files are captured too. Tell the
user the backup ref and the state directory path before the first change.

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
# a. Drop the transaction commits and reset tracked files (backup-protected).
git reset --hard "$start_head"

# b. Delete every non-ignored untracked path, including the ones the
#    transaction created. Step c restores the originals from the backup.
#    `git clean -fd` (never `-x`) leaves ignored content untouched.
git clean -fd

# c. Restore exact worktree content, including untracked files a hook,
#    formatter, or validation command modified or deleted.
rm -f "$state_dir/restore.index"
GIT_INDEX_FILE="$state_dir/restore.index" git -C "$root" read-tree "$worktree_tree"
GIT_INDEX_FILE="$state_dir/restore.index" git -C "$root" checkout-index -a -f

# d. Restore the exact staged/unstaged split.
git read-tree "$index_tree"
git update-index -q --refresh || true
```

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
recovery — remove the backup:

```bash
git update-ref -d refs/prepare-review-commits/backup
rm -rf "$state_dir"
```

If any check fails, stop immediately, change nothing else, keep both
`refs/prepare-review-commits/backup` and `$state_dir`, and report the exact
mismatch together with the manual recovery handle:

```bash
git checkout refs/prepare-review-commits/backup -- .
```

Never claim recovery succeeded without those checks passing.

State these limits rather than papering over them: ignored content is
deliberately left alone, so an ignored artifact written or changed by a hook
or validation command is not reverted; and because Git cannot track an empty
directory, an empty directory that existed before the run is removed by step
(b) and not restored.

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
passed. If it did not, report the mismatch, the retained backup ref
`refs/prepare-review-commits/backup`, and the retained state directory path.

## Do Not

- Activate for a generic "commit my changes" request without explicit
  review-readiness intent.
- Rewrite, amend, or reorder any commit that existed before this workflow ran.
- Run `git fetch`, `git rebase`, `git push`, or any other remote mutation.
- Bypass hooks or commit signing.
- Use interactive commands such as `git add -p`, `git rebase -i`, or anything
  that opens an editor or waits for keyboard input.
- Force-add ignored paths, or run any `git clean` variant with `-x`.
- Run `git reset --hard`, `git clean`, or any other destructive command
  outside the documented, backup-protected recovery procedure.
- Cap the commit count at an arbitrary number.
- Claim recovery succeeded without passing every recovery verification check.
- Treat a clean or ignored-only working tree as a failure.
