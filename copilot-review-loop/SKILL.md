---
name: copilot-review-loop
description: Use when you want GitHub Copilot to review a PR and automatically address its feedback within the current agent session. For any reviewer (human or bot), use pr-review-loop; when an external shell loop should drive one session per comment, use ralph-wiggum-loop.
license: MIT
compatibility: Requires gh CLI. The gh-copilot-review extension is recommended (gh extension install ChrisCarini/gh-copilot-review). PR branch must be checked out locally.
metadata:
  author: Pietro Di Bello
  version: "1.3.0"
allowed-tools: Bash(gh:*)
---

# Copilot Review Loop

## Purpose

Automate an iterative Copilot-driven review loop: trigger a GitHub Copilot
review, address its feedback one comment at a time, then re-trigger Copilot
to review again. Repeat up to 3 cycles until a review finds no critical issues.

This is an **in-session** loop — one long agent context that iterates internally.
It is not the [Ralph Wiggum pattern](https://ghuntley.com/ralph/), which is an
external shell loop that spawns a fresh agent session per comment. For that,
see the `ralph-wiggum-loop` skill instead.

## Typical invocations

Users trigger this skill with prompts like:

- "Request a Copilot review on this PR and address the feedback"
- "Trigger a GitHub Copilot review and fix the issues it finds"
- "Run copilot-review-loop on PR #42"
- "Use copilot-review-loop to get and address Copilot's review comments"

## Prerequisites

- `gh` CLI (required)
- `gh-copilot-review` extension (recommended — see `references/gh-copilot-review-guide.md`)
  ```bash
  gh extension install ChrisCarini/gh-copilot-review
  ```
  Fallback if not installed: `gh pr review --request copilot`
- `pr-review-loop` skill (optional — if installed, the inner loop is delegated to it)
- The PR branch must be checked out locally
- `{tmp}` in the commands below is the directory for temporary files: the session's scratch directory when the harness provides one, otherwise `/tmp`.

## Process

### Step 1 — Pre-flight

Inspect the project for safeguard conventions by checking these files (if they exist):
- `CLAUDE.md`, `AGENTS.md`
- `Makefile`
- `.github/workflows/`
- `README.md`

Identify all required safeguards (tests, compilation, linting, formatting, etc.).
Run all of them. If any fail, stop immediately and report — do not proceed.

### Step 2 — Outer loop (max 3 iterations)

Repeat up to 3 times:

#### 2a. Request Copilot review

Check if `gh-copilot-review` extension is installed:
```bash
gh extension list | grep copilot-review
```

If installed (preferred):
```bash
gh copilot-review [<number> | <url>]
```

If not installed (fallback):
```bash
gh pr review --request copilot
```

#### 2b. Wait for Copilot to complete

Read `references/gh-copilot-review-guide.md` for the polling approach.

Record the current count of unresolved `copilot[bot]` comments before triggering.
Poll every 30 seconds until new comments appear. If no new comments after 10 minutes,
stop and report timeout — do not proceed.

#### 2c. Collect unresolved Copilot comments

Fetch all unresolved comments authored by `copilot[bot]`. Ignore comments from
human reviewers (those are handled by the `pr-review-loop` skill).

Fetch every review comment on the PR once, including the replies. Step 2d
reuses this list.
```bash
gh api --paginate repos/{owner}/{repo}/pulls/{pr}/comments \
  --jq '.[] | {id, in_reply_to_id, user: .user.login, path, line, body, html_url}'
```

The Copilot comments are the entries with `user == "copilot[bot]"` and no
`in_reply_to_id`. Use the count recorded before triggering (step 2b) to identify which are new.

If there are no unresolved Copilot comments, stop — nothing to do.

#### 2d. Skip repeats of earlier answers

Copilot often raises a finding again in a later round after it was already
rejected or parked. Do not triage those findings a second time.

Use the list of comments fetched in step 2c. The earlier answers are
replies (`in_reply_to_id` set) to Copilot comments that are not new in this
round, where the reply rejected the finding
(OUT_OF_SCOPE) or parked it (PARK). Because they are read from the PR, this
also covers rounds from an earlier run of this skill.

A new Copilot comment is a **repeat** when it raises the same concern as one
of those earlier comments, on the same file. The line number may have moved.
If you are not sure that it is the same concern, it is not a repeat: triage
it in step 2e.

A new comment that repeats a finding which was **fixed** is not a repeat in
this sense. Copilot may be pointing at an incomplete fix, so triage it in
step 2e as usual.

For each repeat:

1. Reply with a link to the earlier answer. Skip this if the comment already
   has a reply that links to an earlier answer: a run that stopped before
   step 2 has already posted it.
   ```bash
   cat > "{tmp}/pr-review-reply-{comment_id}.md" <<'EOF'
   This was already raised in an earlier review round and <rejected|parked>: <html_url of the earlier reply>

   <one line: the reason given there>
   EOF

   jq -n --rawfile body "{tmp}/pr-review-reply-{comment_id}.md" '{body:$body}' > "{tmp}/pr-review-reply-{comment_id}.json"

   gh api repos/{owner}/{repo}/pulls/{pr}/comments/{comment_id}/replies \
     --input "{tmp}/pr-review-reply-{comment_id}.json"
   ```
2. Resolve the thread on GitHub.
3. Record it for the "Repeats" section of the summary, and leave it out of
   step 2e.

If every new comment was a repeat, go straight to step 2f.

#### 2e. Address comments — inner loop

**If `pr-review-loop` skill is available:**
Invoke the `pr-review-loop` skill, passing only the Copilot comments collected
in step 2c, minus the repeats skipped in step 2d, as the scope. It will handle triage, one-at-a-time fixes, and replies.

`pr-review-loop` does not reply to the comments that it parks or rejects:
it lists them only in its summary. Step 2d needs those replies to spot
repeats in a later round, so when `pr-review-loop` returns, go through the
Copilot comments in its scope that were classified PARK or OUT_OF_SCOPE. For
each one that has no reply yet:

1. Reply with the classification and the reason given in the triage, for
   example "Rejected: <reason>" or "Parked: <reason>". Use the reply command
   from step 2d.
2. Resolve the thread on GitHub.

**If `pr-review-loop` skill is NOT available:**
Follow this process for each comment that is not a repeat, one at a time (MUST_FIX first, then SHOULD_FIX):

Triage using the five categories defined in `references/triage-guide.md`
(MUST_FIX, SHOULD_FIX, PARK, OUT_OF_SCOPE, NEEDS_CLARIFICATION). Read that file before triaging.

For each MUST_FIX and SHOULD_FIX comment:

1. **Assess complexity:**
   - Trivial (rename, small fix): fix directly
   - Non-trivial: write plan to `.pr-review/plan-<comment-id>.md` first

2. **Run safeguards** — all must pass before touching code

3. **Fix, park, or ask for clarification**
   - Fix or park as usual.
   - If mid-assessment the intent is genuinely ambiguous: post one focused question (see format below), do **not** resolve the thread, skip steps 4–8, move on.

   **Clarification question format:**
   ```bash
   cat > "{tmp}/pr-review-reply-{comment_id}.md" <<'EOF'
   Thanks for the feedback! Before I make a change, I want to make sure I understand what you're after:

   <one specific, focused question>
   EOF

   jq -n --rawfile body "{tmp}/pr-review-reply-{comment_id}.md" '{body:$body}' > "{tmp}/pr-review-reply-{comment_id}.json"

   gh api repos/{owner}/{repo}/pulls/{pr}/comments/{comment_id}/replies \
     --input "{tmp}/pr-review-reply-{comment_id}.json"
   ```

   Ask exactly **one** question. Leave the thread unresolved so the reviewer's answer re-surfaces it.

4. **Run safeguards again** — all must pass

5. **Commit and push:**
   ```bash
   git add <changed files>
   git commit -m "<conventional commit describing the fix>"
   git push
   ```

6. **Reply to the comment** — explain fix, deferral, or rejection

7. **Resolve the comment on GitHub**

8. **Delete plan file** if one was created:
   ```bash
   rm .pr-review/plan-<comment-id>.md
   ```

#### 2f. Check stop conditions

Stop iterating if any of:
- This pass found no MUST_FIX Copilot comments: the review has converged
- A MUST_FIX Copilot comment from this pass is still unresolved (for example, its fix failed the safeguards): report it in the summary instead of starting another round
- Only OUT_OF_SCOPE or NEEDS_CLARIFICATION Copilot comments remain (awaiting reviewer input)
- This was the 3rd iteration: the review did not converge, so step back (see below)

Repeats skipped in step 2d are never triaged, so they never count as MUST_FIX
here. A pass that found only repeats has converged.

Otherwise (this pass found MUST_FIX comments and all of them are now fixed),
continue to the next iteration (back to step 2a) so Copilot can check the fixes.

**Step back when the cap stops the loop.** Three rounds that each still find
MUST_FIX issues suggest that the approach is the problem, not the individual
lines. Do not start a 4th round. Instead:

1. Group the MUST_FIX and SHOULD_FIX comments from all rounds by kind of
   finding (for example "missing error handling", "unvalidated input",
   "race on shared state"). Name the kind after the problem, not the file.
2. List each kind that showed up in more than one round, with the round
   numbers and the comment IDs for each.
3. Suggest how the approach could change so that the whole kind goes away,
   for example a different design, a shared helper, or a test that covers
   the case. Present these as suggestions for the user to decide on. Do not
   apply them.

Put this in the "Not converged" section of the summary (Step 3), and tell
the user in the session as well.

### Step 3 — Summary

Post a final comment on the PR:

```
## Copilot Review Loop — Summary

Completed N Copilot review cycle(s).

### Fixed
- [commit abc1234] <description> (Copilot comment #<id>)
- ...

### Parked
- <description> — deferred, tracked in #<issue>
- ...

### Rejected
- <description> — <reason>
- ...

### Repeats
- <description> — already <rejected|parked> in <link to earlier reply> (Copilot comment #<id>)
- ...

### Awaiting Clarification
- Asked Copilot: "<question>" — thread left open (comment #<id>)
- ...

### Unresolved MUST_FIX
- <description> — <why it could not be fixed> (Copilot comment #<id>)
- ...

### Not converged
Stopped at the 3-round cap while Copilot was still finding MUST_FIX issues.
Kinds of finding that kept coming back:
- <kind> — rounds <n>, <m> (Copilot comments #<id>, #<id>)
- ...
Consider: <suggested change of approach>
```

Omit any section that has no entries.

## Resumability

This skill can be interrupted and restarted in a fresh context at any point.

On restart:
1. Run pre-flight (Step 1)
2. Check for an existing `.pr-review/plan-*.md` — if found, continue mid-fix from step 2e
3. Re-fetch unresolved Copilot comments — already-resolved ones won't appear
4. Continue the outer loop from the current state

## State Directory

`.pr-review/` at the repo root (should be gitignored by the project).
- `plan-<comment-id>.md` — plan for the comment currently in progress (deleted after resolution)

## Do Not

- Bundle all PR feedback into one large commit
- Make multiple unrelated changes in a single commit
- Push all changes at once without intermediate commits
- Leave Copilot comments unresolved after addressing them
- Proceed to the next Copilot review cycle if MUST_FIX items remain unresolved
