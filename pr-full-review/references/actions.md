# Post-Review Actions

Read this reference only after the user selects an action at Step 4. Execute
strictly what the user approved.

## Action A: Fix selected items locally now

Use this when the user wants to address selected findings directly on the
current PR branch instead of (or before) posting GitHub review threads.

### 1. Discover and run safeguards

Inspect `AGENTS.md`, `CLAUDE.md`, `Makefile`, `Makefile.toml`, and
`.github/workflows/` to find the repository's documented formatting, linting,
build, test, and completion commands, plus commit subject conventions.

Offer to skip the upfront baseline run only when CI is already green on local
`HEAD` and the working tree is clean:

```bash
gh pr view --json headRefOid,statusCheckRollup --jq '{head: .headRefOid, checks: (.statusCheckRollup | length), green: ((.statusCheckRollup | length) > 0 and all(.statusCheckRollup[]; (.conclusion // .state) as $r | ($r == "SUCCESS" or $r == "NEUTRAL" or $r == "SKIPPED")))}'
git rev-parse HEAD
git status --porcelain
```

Never skip the upfront baseline without the user's answer. Skipping replaces
only the upfront run; per-fix and final completion checks still apply.

### 2. Protect existing work

Before editing, snapshot `git status --short` and build a **never-stage list**
of any pre-existing unrelated dirty or untracked files, local environment files,
or scratch files. Never run `git add -A`, `git add .`, or `git commit -a`;
always stage explicit paths with `git add -- <path>...`.

### 3. Implement one focused commit per approved finding (or cascade)

Process approved findings in severity order (`high`, then `medium`, then `low`).
Group findings into one commit only when they form a single atomic cascade.

For each finding:

1. For bug fixes, add or update a test that reproduces the issue first, then fix
   the production code until it passes.
2. Run the smallest relevant test/check suite for fast feedback.
3. Review `git diff` to confirm the change matches the approved finding without
   unrelated edits.
4. Stage only the intended files (`git add -- <path>...`) and commit with a
   Conventional Commit message matching the repository's conventions.

### 4. Final verification and hand-back

After the last approved fix:

1. Run the repository's documented completion gate (format, lint, full test
   suite, and any workspace checks). Fix any regression before reporting done.
2. Check whether the commits drifted the PR's scope away from the PR body; if
   so, mention the drift and offer to update the PR body (do not edit it without
   asking).
3. Report each commit SHA + subject, exact verification commands run and their
   results, any deferred items, and state explicitly that nothing was pushed
   (push only when the user asks).

---

## Action B: Post selected findings as inline review threads on GitHub

Use this when the user wants selected findings published on the PR for
discussion or follow-up.

### 1. Verify every target line sits inside the PR diff

GitHub's Pull Request Review API rejects inline comments whose `line` is not
part of a diff hunk. Compute the valid `RIGHT`-side line ranges from the diff
at `headRefOid`, the commit that the review is posted on. Do not use local
`HEAD`: it differs from `headRefOid` when local fixes are not pushed yet.

```bash
python3 - <<'EOF'
import re, subprocess
diff = subprocess.check_output(["git", "diff", "origin/<base>...<headRefOid>"]).decode()
cur_file, hunks = None, {}
for line in diff.splitlines():
    if line.startswith("+++ b/"):
        cur_file = line[6:]
        hunks[cur_file] = []
    elif line.startswith("@@ "):
        m = re.search(r"\+(\d+)(?:,(\d+))?", line)
        start = int(m.group(1))
        count = int(m.group(2)) if m.group(2) is not None else 1
        hunks[cur_file].append((start, start + count - 1))
for path, ranges in hunks.items():
    print(path, ranges)
EOF
```

If an approved finding lives outside the PR diff (for example, a stale test mock
broken by a changed signature in the diff), anchor the inline comment to the
diff line that triggered the issue and cite the exact out-of-diff `file:line` in
the comment body.

### 2. Format the review payload

Write the review JSON to a temporary file in `{tmp}` (the session scratch
directory when available, otherwise `/tmp`) so shell quoting never corrupts
Markdown:

- `commit_id`: exact `headRefOid` of the PR.
- `event`: `"COMMENT"` (safe for both own PRs and others' PRs; use
  `"REQUEST_CHANGES"` only if the user explicitly asks).
- `body`: concise summary naming the reviewed SHA, CI status, count of threads
  by class, and a one-line duplication summary.
- `comments`: array of `{ "path", "line", "side": "RIGHT", "body" }`, each
  starting with `**<Class> (<severity>): <one-line title>.**`, followed by the
  verified evidence and minimal suggested fix or focused question.
- Respect the user's writing preferences (for example, plain scannable prose
  without em-dashes when configured).

### 3. Submit once and verify via GET

POST the review atomically (never re-run POST to verify, as that creates
duplicate reviews):

```bash
gh api --method POST \
  "repos/{owner}/{repo}/pulls/{pr_number}/reviews" \
  --input "{tmp}/pr-full-review-{pr_number}.json" \
  > "{tmp}/pr-full-review-{pr_number}-response.json"
```

Verify the posted review and every created thread via `GET`. The review's own
comments endpoint returns no `line` or `side`, so filter the PR's comments by
review ID instead:

```bash
review_id="$(jq '.id' "{tmp}/pr-full-review-{pr_number}-response.json")"
gh api "repos/{owner}/{repo}/pulls/{pr_number}/comments" --paginate \
  --jq ".[] | select(.pull_request_review_id == ${review_id}) | \"\(.id) \(.path):\(.line) \(.side) \(.html_url)\""
```

Report the review URL and every posted thread link back to the user.

## Action C: Split (fix some locally, post others on GitHub)

Ask or confirm order before acting:

- If the user wants threads only for items **not** fixed locally (such as open
  product questions or design trade-offs), verify whether the local fixes move
  line numbers on files receiving threads. Either post the threads against the
  current `headRefOid` first (before committing local fixes), or commit and push
  local fixes first (if the user approves pushing) and post threads against the
  new `headRefOid`.
