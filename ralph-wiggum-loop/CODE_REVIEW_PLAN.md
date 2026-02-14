# Code Review Plan

You are one iteration of an automated PR code review loop.
Each invocation, you do exactly **one unit of work**, then stop.
An external loop will re-invoke you in a fresh context for the next unit.

---

## What to do

Check whether `PR_COMMENTS_PLAN.md` exists in the current directory.

- **Does not exist** → run **Initialize** below.
- **Exists** → run **Fix one comment** below.

---

## Initialize (first run only)

1. Identify the current PR:
   ```bash
   gh pr view --json number,title,url,headRefName
   ```

2. Fetch all review comments:
   ```bash
   gh api repos/{owner}/{repo}/pulls/{pr}/comments \
     --jq '.[]'
   ```
   > **Note:** The GitHub REST API does not expose a `.resolved` field on review comment objects; unresolved status is tracked in `PR_COMMENTS_PLAN.md`.

3. Triage every comment into one of:
   - **MUST_FIX** — correctness bug, security flaw, broken build, or data loss risk
   - **SHOULD_FIX** — non-blocking improvement worth addressing in this PR
   - **PARK** — valid concern but out of scope; will open a follow-up issue
   - **OUT_OF_SCOPE** — does not apply to this code; reply with reasoning

4. Write `PR_COMMENTS_PLAN.md` (see format at the bottom of this file).

5. **Stop.** Do not fix anything on the first run.
   The external loop will re-invoke you with a fresh context.

---

## Fix one comment

1. Read `PR_COMMENTS_PLAN.md`. Find the topmost unresolved item:
   - First: any MUST_FIX with `[ ]`
   - Then: any SHOULD_FIX with `[ ]`
   - If none remain → write the file `PR_REVIEW_DONE` and print:
     `"All comments addressed. Stopping loop."` then stop.

2. Check for a `.pr-review/plan-<comment-id>.md` file — if it exists, a
   previous session was interrupted mid-fix. Skip to step 5.

3. Discover project safeguards by inspecting (if they exist):
   `CLAUDE.md`, `AGENTS.md`, `Makefile`, `.github/workflows/`, `README.md`

   Identify all required checks: tests, linting, compilation, formatting, etc.
   Run all of them. If any fail, **stop and report** — do not touch code.

4. Assess the fix complexity:
   - Trivial (rename, one-liner, obvious fix): fix directly.
   - Non-trivial: write a brief plan to `.pr-review/plan-<comment-id>.md` first.

5. Implement the fix.

6. Run all safeguards again. If any fail, revert your changes and report.

7. Commit and push:
   ```bash
   git add <changed files>
   git commit -m "<type>(<scope>): <description addressing the comment>"
   git push
   ```

8. Reply to the comment on GitHub explaining what you changed and why.

9. Resolve the comment on GitHub.

10. Update `PR_COMMENTS_PLAN.md`:
    - Change `[ ]` to `[x done: <commit-hash>]` for the comment you fixed.

11. Delete `.pr-review/plan-<comment-id>.md` if you created one.

12. **Stop.** Do not fix any other comments.
    The external loop will re-invoke you with a fresh context.

---

## PARK handling

1. Reply to the comment explaining why it is out of scope for this PR.
2. Open a GitHub issue to track it:
   ```bash
   gh issue create --title "<brief description>" --body "<context>"
   ```
3. In `PR_COMMENTS_PLAN.md`, mark the item as `[parked → #<issue>]`.
4. **Stop.**

---

## OUT_OF_SCOPE handling

1. Reply to the comment explaining why it does not apply.
2. In `PR_COMMENTS_PLAN.md`, mark the item as `[rejected: <reason>]`.
3. **Stop.**

---

## PR_COMMENTS_PLAN.md format

```markdown
# PR Comments Plan
PR: #<number> — <title>
URL: <url>
Fetched: <date>

## MUST_FIX
- [ ] <comment-id> — <description> — <file>:<line>
- [x done: abc1234] <comment-id> — <description> — <file>:<line>

## SHOULD_FIX
- [ ] <comment-id> — <description>

## PARK
- [parked → #88] <comment-id> — <description>

## OUT_OF_SCOPE
- [rejected: unrelated to this PR] <comment-id> — <description>
```

Keep the list ordered: topmost items are addressed first.
Do not reorder items between sessions.
