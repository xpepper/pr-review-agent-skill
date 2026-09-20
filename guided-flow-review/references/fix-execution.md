# Executing an accepted fix

Read this when the user asks to fix a finding, during the review or after it.
A fix request is strictly scoped to the specific requested item; never treat it
as a standing fix-as-we-go mode for subsequent items or steps.

## Prepare before the first fix

From the repository instructions, collect the formatting, linting, build, test,
and completion commands; commit subject and trailer rules; and files that are
generated or must not be edited. If the repository requires a preflight before
code changes, run it now, then re-check `git status --short` and attribute any
newly generated files.

Snapshot the working tree:

```bash
git status --short
git diff --name-status
git diff --cached --name-status
git stash list
```

Classify dirty paths by name as part of the reviewed change or unrelated author
work before printing any patch, and never render credential or environment
files. Build a **never-stage list**: unrelated dirty or untracked paths, local
environment and credential files, the review TODO, and anything the repository
says must not be committed.

Pick the fix baseline by review mode:

- **PR or branch**: commit on the checked-out branch.
- **Working tree**: edit in place without committing, unless the user
  establishes a committed baseline or approves committing the whole affected
  change.
- **Explicit range**: fix only when the range ends at `HEAD` and the user
  approves that checkout; otherwise the checkout is not the reviewed code, so
  leave the item in the TODO.

## Protect the author's work

- Prefer fixing a file that had no pre-existing unrelated modifications.
- If a target file already contains unrelated author work, ask the user to
  stash or commit it first, or keep this fix uncommitted.
- Forbid `git commit -a`, pathless `git add`, and `git add -A`: each can sweep
  unrelated author work or the review TODO into a review commit.
- Stage only explicit intended paths or hunks, always after an end-of-options
  delimiter: `git add -- <path>...` or `git add -p -- <path>`.

## Implement one improvement

One accepted improvement produces one focused, green commit in branch/PR mode.
A test-first change may go red locally, but the failing test and production fix
land together; do not publish a broken intermediate commit.

For characterization tests, perform a mutation check: temporarily break the
production behavior, observe the new test fail for the intended reason, restore
the production code, and observe it pass. Mutate only a file with no
uncommitted changes, and set the TODO's `In flight` field to its path before
editing, so an interrupted session knows what to undo. On every outcome,
including a failed or interrupted command, restore it with
`git restore -- <file>`, confirm `git diff --quiet -- <file>`, then reset the
field to `none`.

Delegate a self-contained fix when an implementation agent is available and
the work is separable. Its prompt must include:

- exact target behavior and files;
- relevant repository instructions;
- expected test-first or characterization approach;
- never-stage paths and the pre-existing dirty-file snapshot;
- explicit staging paths after `--`; no broad staging;
- formatter, targeted checks, and documented completion command;
- expected commit subject and active trailer policy;
- instruction not to push.

Use one writer at a time: two writers share one index and working tree, so
their staging and edits interleave. While a delegated fix runs, continue only
read-only review of files it cannot touch. Avoid index-writing or
worktree-changing git commands, and never run two fixes concurrently.

## Verify the hand-back

Snapshot HEAD before delegation or editing. Afterwards:

1. Confirm the new commit's parent is the expected HEAD; report rebases,
   amendments, or parallel author commits.
2. Inspect `git show --stat --oneline <sha>`.
3. Confirm the commit file list equals the intended list and that never-stage
   paths and the review TODO are absent; if not, stop without printing the
   patch.
4. Inspect the full patch and compare removed and added assertions so coverage
   was not silently traded away.
5. Run formatting and targeted tests/checks, then re-run `git status --short`.
   Commit intended formatter changes to the fix before recording it, and
   classify any other new path; never record a SHA while its output is dirty.
6. Run the repository's documented completion gate after a delegated hand-back
   and report test/check counts when available. For direct edits, follow the
   same repository gate policy. The review also runs the full gate at close.
7. Record SHA plus commit subject in Done and remove or move the source item.

If a later fix changes an already reviewed file, mark the affected step for a
short re-review and identify those hunks as review-generated.
