# Executing an accepted fix

Read this when the user asks to fix a finding, during the review or after it.

## Protect the author's work

Before the first fix, resolve unrelated working-tree changes:

- Prefer fixing a file that had no pre-existing unrelated modifications.
- If a target file already contains unrelated author work, ask the user to
  stash or commit it first, or switch this review to edit-only mode.
- Forbid `git commit -a`, pathless `git add`, and `git add -A`.
- Stage only explicit intended paths or hunks, always after an end-of-options
  delimiter: `git add -- <path>...` or `git add -p -- <path>`.

In working-tree mode, edit in place without committing by default. Create
review commits only after the user establishes a committed baseline or
explicitly approves committing the whole affected change.

In a read-only range review, record an accepted fix under Open and do not edit.

## Implement one improvement

One accepted improvement produces one focused, green commit in branch/PR mode.
A test-first change may go red locally, but the failing test and production fix
land together; do not publish a broken intermediate commit.

For characterization tests, perform a mutation check: temporarily break the
production behavior, observe the new test fail for the intended reason, restore
the production code, and observe it pass. Mutate only a file with no
uncommitted changes, and note the mutated path under Open before editing. On
every outcome, including a failed or interrupted command, restore it with
`git restore -- <file>`, confirm `git diff --quiet -- <file>`, then remove the
note. On resume, restore any file that note still names before anything else.

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

Use one writer at a time. While a delegated fix runs, continue only read-only
review of files it cannot touch. Avoid index-writing or worktree-changing git
commands, and never run two fixes concurrently.

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
   same repository gate policy. Always run the full completion gate at close.
7. Record SHA plus commit subject in Done and remove or move the source item.

If a later fix changes an already reviewed file, mark the affected step for a
short re-review and identify those hunks as review-generated.
