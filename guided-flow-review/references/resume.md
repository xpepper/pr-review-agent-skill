# Resuming a guided review

Read this when a review TODO for the same target already exists.

1. If the `In flight` field names a file, a mutation check was interrupted:
   restore it with `git restore -- <file>`, confirm
   `git diff --quiet -- <file>`, and reset the field to `none` before anything
   else.
2. Reuse its pinned comparison.
3. Compare current HEAD and changed paths with its recorded start.
4. If history was rewritten (rebase, amended or missing commits), stop and
   report it. Ask whether to re-pin the comparison; on re-pin, record the new
   pins and reopen Review progress steps whose files differ under it.
5. Preserve completed decisions and commit subjects. A subject keeps a Done
   item understandable when its SHA changed.
6. Append newly changed files to Review progress.
7. Resume at the first unchecked step.
