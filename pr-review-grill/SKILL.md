---
name: pr-review-grill
description: Use when addressing open pull-request review comments and the user wants to discuss, challenge, and decide each comment one at a time before any code changes. Trigger for requests to grill review feedback, walk through comments individually, debate whether comments are valid, or work through PR feedback collaboratively. Do not use this skill for fast batch triage; use pr-review-loop instead.
license: MIT
compatibility: Requires gh CLI or another GitHub client, jq, and the PR branch checked out locally.
metadata:
  author: Pietro Di Bello
  version: "0.1.0"
allowed-tools: Bash(gh:*)
---

# PR Review Grill

## Purpose

Address open PR review comments through an evidence-led conversation. Discuss one
comment at a time, test its premises against the codebase and project
conventions, and do not move to the next comment until the user and agent agree
on the classification and intended action.

This is deliberately slower than `pr-review-loop`. The value is judgment:
review feedback is treated as a claim to examine, not an instruction to accept
blindly. User corrections about domain facts, project conventions, or intended
scope are first-class evidence and must update the assessment.

## Non-negotiable boundaries

- Complete pre-flight before changing code or posting remote replies.
- Collect both unresolved review threads and top-level issue comments.
- Do not discard substantive inline comments merely because their author is a
  bot. Ignore only automated summaries, notifications, and non-actionable
  acknowledgments.
- Discuss exactly one comment or confirmed cascade at a time.
- Persist the decision immediately after each discussion.
- Do not edit code, create plans, reply, resolve, commit, or push until every
  feedback item has a recorded decision and the user gives final approval.
- Never turn an unresolved premise into a silent assumption. State the premise,
  show the evidence, and invite correction.
- Never use `git reset --hard`, `git checkout --`, or other destructive commands.
- Do not revert changes that predate this run.

## Prerequisites

- `gh` CLI is preferred.
- The PR branch must be checked out locally.
- The repository's documented safeguards must be discoverable and runnable.
- The `.pr-review/` directory must be gitignored before writing persistent
  triage state. If it is not ignored, ask the user before creating state there.

## State and resumability

Use `.pr-review/triage.json` as the durable ledger. See
[references/triage-state.md](references/triage-state.md) for the schema.

Write state after:

- feedback collection;
- selecting the current item;
- every user correction;
- every classification or action decision;
- final triage approval;
- every commit, reply, and resolution.

The state is local workflow data, not a replacement for GitHub. On resume,
re-fetch GitHub feedback and compare it with the ledger. Preserve prior
decisions, but verify remote replies, thread resolution, branch commits, and
the current PR body before continuing.

## Process

### 1. Pre-flight

Inspect the project for safeguards in files that exist:

- `CLAUDE.md`
- `AGENTS.md`
- `Makefile` or `Makefile.toml`
- `.github/workflows/`
- `README.md`

Identify required formatting, linting, compilation, tests, dependency checks,
and workspace-specific commands. Run the documented baseline safeguards before
touching application code. If the baseline fails, stop and report the failure;
do not use review feedback as an excuse to work on a broken baseline.

Documentation-only changes may be exempt when the repository explicitly says
so, but follow the repository's rule rather than assuming an exemption.

### 2. Identify the PR

Run:

```bash
gh pr status
gh pr view
```

Confirm the current branch is the PR head. Record owner, repository, PR number,
base branch, head branch, author, title, and current body in the state ledger.

### 3. Collect all unresolved feedback

Collect both review threads and issue comments. Review threads have a resolve
operation; issue comments do not.

For review threads, fetch at least:

- thread ID and resolution state;
- path, line, and start line;
- every comment in the thread;
- author, database ID, body, creation time, and reply relationship.

For issue comments, fetch:

- comment ID;
- author;
- body;
- creation time.

Filter out comments authored by the PR author when they are not reviewer
feedback. Keep substantive comments from automated reviewers. Filter only
obvious bot summaries, status notifications, duplicate acknowledgments, and
emoji-only comments when they do not contain a request or claim to assess.

Normalize each item with a stable key:

- `review-thread:<thread-id>` for inline threads;
- `issue-comment:<comment-id>` for top-level comments.

Keep the original remote IDs. They are required later for replies and
resolution.

### 4. Prepare the discussion queue

Create or load `.pr-review/triage.json`. Re-fetching after an interruption must
not reset items whose decisions are already recorded.

Group comments only when they are clearly one cascade or the same underlying
issue. Do not group merely because they touch the same file. A grouping must be
shown to the user and confirmed before it is treated as one decision.

Order the queue as:

1. blocking correctness, security, data-isolation, or explicit merge blockers;
2. worthwhile non-blocking improvements;
3. valid deferred concerns;
4. suggestions that may be rejected;
5. genuinely ambiguous items.

This is an initial discussion order, not a pre-classification. The user may
change it.

### 5. Grill one item at a time

For the current item, present an evidence card and then stop for the user's
response. Do not show a batch triage table before the individual discussions.

Use this structure:

```markdown
### Comment <n>/<total> — <author> `<path>:<line>`

**Feedback**
> <short quotation or faithful summary>

**Code and convention evidence**
- <relevant implementation fact>
- <relevant test, schema, documentation, or project convention>

**Premise check**
<State the assumption the comment depends on. Say whether it is verified,
unsupported, or contradicted. Include uncertainty explicitly.>

**Provisional assessment**
<Recommend a classification and explain the strongest argument against it.>

**Decision**
<Ask for the user's classification or the one fact needed to decide it.>
```

The assessment should challenge both sides:

- Could the reviewer be identifying a real correctness, security, or data
  contract problem?
- Is the concern based on a false premise, a different scope, or a convention
  the repository intentionally does not follow?
- Does the requested change alter a public API or architecture enough to need
  team discussion?
- Is the concern already handled by a stronger invariant elsewhere?
- Can the proposed fix be made safely within this PR?

#### Bounded discussion loop

The default mode is bounded, not adversarial. Continue the current item until:

- the user confirms or corrects the premise;
- the classification is explicit;
- the intended action is explicit; and
- any implementation preference or deferral reason is recorded.

If the user challenges a premise, update the evidence and reassess instead of
defending the original recommendation. If the user supplies a durable
codebase/domain fact, record it in the triage state and use it for later items.

Ask at most one focused question per turn. Do not ask a generic "what do you
think?" when a concrete choice or missing fact is available. Do not advance to
the next item while the current one has multiple materially different
interpretations.

### 6. Record the decision

Every item or confirmed cascade must record:

- classification;
- rationale grounded in evidence;
- whether the feedback is accepted, adapted, parked, rejected, or awaiting
  clarification;
- implementation notes or the reason no implementation is planned;
- remote action, if any;
- comment IDs and grouped item keys.

Use these classifications from
[references/triage-guide.md](references/triage-guide.md):

- `MUST_FIX`
- `SHOULD_FIX`
- `PARK`
- `OUT_OF_SCOPE`
- `NEEDS_CLARIFICATION`

Do not use `NEEDS_CLARIFICATION` merely to avoid difficult work. Use it only
when choosing an interpretation without the reviewer's answer risks a
meaningfully different change.

After recording a decision, show a one-line confirmation and move to the next
item. Repeat the evidence-card discussion for every unresolved item.

### 7. Final triage approval

When every item has a decision, present the completed ledger in a compact table.
Include any user overrides and confirmed cascades.

Stop and ask for explicit approval before processing. Until approval:

- do not edit files;
- do not create plan files;
- do not post replies;
- do not resolve threads;
- do not commit or push.

If the user changes a decision, update the ledger and re-present only the
affected entry unless the change alters the overall processing order.

### 8. Process approved decisions

Process `MUST_FIX` first, then `SHOULD_FIX`. Process cascades atomically, with
one focused commit per cascade. `PARK`, `OUT_OF_SCOPE`, and
`NEEDS_CLARIFICATION` items follow the action recorded during discussion.

#### Fixes

For each fix:

1. Assess complexity. Trivial edits need no plan; non-trivial edits need
   `.pr-review/plan-<comment-id>.md` before code changes.
2. Run the required safeguards before editing.
3. Implement the smallest complete fix, including tests and documentation
   directly required by the change.
4. Run the safeguards again and fix regressions before continuing.
5. Commit one focused change with a Conventional Commit subject and a body
   naming the reviewer.
6. Push the commit.
7. Reply to the original comment, explaining what changed, any adaptation, and
   the commit.
8. Verify the posted reply with a GET using the response ID. Never re-POST to
   verify.
9. Resolve the review thread only after the reply is verified. Issue comments
   have no resolve operation; the verified reply is their closure signal.
10. Update the ledger and delete the plan file.

Use body files for GitHub replies and PR comments. Do not rely on inline shell
strings for Markdown containing quotes, backticks, or special characters.

#### Parked items

Do not implement a parked concern. Record why it is deferred and whether a
follow-up issue is required. Create a follow-up issue only when the user has
approved that action; do not invent issue numbers or silently expand scope.
Leave the original review thread open unless the user explicitly chooses a
different remote action.

#### Out-of-scope items

Do not change code. If the user chose to reply, explain the factual reason and
whether the suggestion conflicts with an established invariant or scope.
Resolve the thread only when the user chose resolution. A genuine rejected
suggestion is different from a no-op acknowledgment; do not force both through
the same response.

#### Clarification items

Post exactly one focused question to the reviewer, leave the thread unresolved,
and record the question in the ledger. Do not implement or resolve the item.

### 9. Check PR body drift

After processing fixes, compare all commits on top of the PR base with the
current PR body:

```bash
base=$(gh pr view <pr-number> --json baseRefName --jq '.baseRefName')
git log "origin/$base..HEAD" --oneline
gh pr view <pr-number> --json body --jq '.body'
```

Update the body only when it would mislead a reader about the complete PR
scope. Do not churn the body for pure bug-fix tweaks.

### 10. Post and verify the summary

Post one final PR comment using a body file:

```markdown
## PR Review Grill — Summary

### Fixed
- [commit <sha>] <change> (comment by @<reviewer>)

### Parked
- <deferred concern and reason> (comment by @<reviewer>)

### Rejected
- <reasoned rejection> (comment by @<reviewer>)

### Awaiting Clarification
- Asked @<reviewer>: "<question>" — thread left open

### PR Body
- Updated the body to reflect <scope change>
```

Omit empty sections. Verify the posted summary with `gh pr view <pr-number>
--comments`, then update the ledger to `complete`.

## Resume behavior

On a fresh invocation:

1. Run pre-flight.
2. Identify the current PR and re-fetch feedback.
3. Load `.pr-review/triage.json`.
4. Verify any prior commit, reply, resolution, and summary remotely.
5. If an item is `discussing`, resume that item rather than silently skipping
   it.
6. If all items are decided but final approval is missing, show the ledger and
   ask for approval again.
7. If processing is in progress, continue at the first unverified action.

Never infer that a remote write succeeded from a local command timeout. Re-fetch
the remote object before retrying, because repeating a POST can create duplicate
replies or summaries.

## Do not

- Batch-triage all comments before discussing the first one.
- Start implementation before the final triage approval.
- Treat bot authorship as a reason to ignore substantive feedback.
- Continue debating after the user has given a clear, recorded decision.
- Bundle unrelated feedback into one commit.
- Resolve a thread without verifying the reply and intended resolution.
- Leave the ledger claiming completion when parked or clarification threads are
  still intentionally open.
