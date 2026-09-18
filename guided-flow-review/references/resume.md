# Resuming a guided review

Read this when a review TODO for the same target already exists.

1. Reuse its pinned comparison.
2. Compare current HEAD and changed paths with its recorded start.
3. If history was rewritten (rebase, amended or missing commits), stop and
   report it. Ask whether to re-pin the comparison; on re-pin, record the new
   pins and reopen Review progress steps whose files differ under it.
4. Preserve completed decisions and commit subjects. A subject keeps a Done
   item understandable when its SHA changed.
5. Append newly changed files to Review progress.
6. Resume at the first unchecked step.
