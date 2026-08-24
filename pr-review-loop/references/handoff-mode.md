# PR Review Loop — Handoff Mode

Handoff mode keeps each conversation inside a narrow working set. One session
triages feedback or completes one approved action, records durable state, and
stops. The user starts the next session explicitly.

This mode is experimental. Use the normal workflow in `../SKILL.md` for shared
classification, safeguard, commit, reply, resolution, and PR-body rules unless
this reference overrides a boundary or state rule.

## Contents

- [Non-negotiable boundaries](#non-negotiable-boundaries)
- [State file](#state-file)
- [Required handoff structure](#required-handoff-structure)
- [Item identity and states](#item-identity-and-states)
- [Start of every invocation](#start-of-every-invocation)
- [Unit 1 — Initial triage](#unit-1--initial-triage)
- [Unit 2 — Delta triage](#unit-2--delta-triage)
- [Unit 3 — Process one approved item](#unit-3--process-one-approved-item)
- [Unit 4 — Finalization](#unit-4--finalization)
- [Final response for every unit](#final-response-for-every-unit)

## Non-negotiable boundaries

- Activate this mode only when the user explicitly requests `--handoff` or
  equivalent wording in the current session.
- Use one local checkout and one active handoff agent at a time. Do not add
  locking or run overlapping sessions.
- Complete exactly one unit per session:
  - initial or delta triage;
  - one approved comment action or confirmed atomic cascade;
  - one finalization pass.
- Stop after the unit even when more context appears available.
- A cascade is one item only when applying one comment alone would leave the
  code inconsistent. Do not batch merely related comments for convenience.
- Do not migrate an in-progress normal-mode run automatically. If normal-mode
  plan files or unexplained partial edits exist without handoff state, stop and
  ask the user to choose which workflow owns them.
- Treat git, GitHub, and verification commands as evidence. The handoff is a
  compact index of verified state, not a replacement for those sources.

## State file

Use `.pr-review/HANDOFF.md` as the only durable handoff artifact.

Before creating it:

1. Create `.pr-review/` if needed.
2. Check whether `.pr-review/` is ignored.
3. Resolve the worktree-safe exclude path with:
   ```bash
   git rev-parse --git-path info/exclude
   ```
4. If `.pr-review/` is not ignored, add this exact entry to that exclude file:
   ```
   .pr-review/
   ```
5. Confirm the handoff will not appear as an untracked commit candidate.

Do not modify the tracked `.gitignore` for this local workflow state.

The file is agent-owned and human-readable. Update it before editing code and
immediately after every irreversible milestone. Prefer an atomic replacement
through a temporary file in `.pr-review/` so interruption cannot leave a
partially written ledger.

Keep it compact:

- store stable remote IDs and short summaries rather than full comment bodies;
- store concise test results rather than raw logs;
- store relevant paths rather than diffs;
- compact completed items to one line;
- target roughly 500–2,000 tokens, while retaining every queue item when a large
  PR genuinely needs more.

## Required handoff structure

Maintain these sections:

```markdown
# PR Review Handoff

Status: awaiting-approval | ready | in-progress | ready-to-finalize | complete
Cycle: <number>
Repository: <owner>/<repo>
PR: #<number> — <title>
Head branch: <branch>
PR author: @<login>
Last synchronized: <timestamp>
Triage approved: <timestamp or "not approved">

## Objective
<one short paragraph>

## Safeguards
- Required: `<command>`, ...
- Last verified commit: <sha or "not run">
- Result: <concise result>

## Queue
| Key | Remote refs | Class | Approved action | State | Summary |
|-----|-------------|-------|-----------------|-------|---------|
| review-thread:<thread-id> | comment <id>, version <fingerprint> | MUST_FIX | fix, reply, resolve | pending | ... |

## Current item
- Key: <stable key or "none">
- Base commit: <sha>
- Plan: <smallest complete approach>
- Expected paths: <paths>
- Checkpoints: <verification, commit, push, reply ID, resolution>
- Known failure: <concise failure or "none">

## Completed this cycle
- <stable key> — <terminal state and evidence>

## Summaries
- <cycle> — <GitHub comment ID and URL>

## Next action
<exactly one concrete action for the next fresh session>
```

Keep `## Next action` last so the next agent sees the critical instruction near
the end of the retrieved state.

Bind the file to repository, PR number, and head branch. If the current checkout
points to a different PR or branch, do not overwrite or reuse the file. Tell the
user to archive or remove it first.

## Item identity and states

Use stable keys:

- `review-thread:<thread-id>` for inline review threads;
- `issue-comment:<comment-id>` for top-level PR conversation comments.

Preserve the original comment IDs needed for replies, plus every workflow reply,
summary, and follow-up issue ID. This prevents the workflow's own top-level
comments from being rediscovered as reviewer feedback.

For each known item, also preserve a compact remote version fingerprint using
the latest available `updatedAt` value and ordered comment/reply IDs. Use it to
detect material edits and new replies without copying full bodies into the
handoff.

Use concise item states:

- `needs-triage`
- `awaiting-approval`
- `pending`
- `in-progress`
- `asked`
- `done`
- `parked`
- `rejected`
- `acknowledged`
- `resolved-externally`
- `removed`
- `needs-retriage`

`asked` is terminal for the current cycle. A later substantive reviewer reply
changes the same item to `needs-retriage`; it does not create a duplicate item.

## Start of every invocation

1. Load the handoff when it exists and verify repository, PR, and branch
   identity.
2. Re-fetch all GitHub feedback before choosing work.
3. Reconcile remote state, local git state, and recorded checkpoints.
4. Choose exactly one unit using the rules below.

Choose in this order:

1. resume an `awaiting-approval` initial or delta triage, first folding in any
   newly reconciled `needs-triage` or `needs-retriage` items into that same
   pending table before presenting it;
2. delta-triage any `needs-triage` or `needs-retriage` item;
3. resume the recorded `in-progress` item;
4. process the next approved pending item;
5. finalize when no action remains.

If the handoff is `complete` and reconciliation finds no delta, report that the
workflow is complete and stop without posting another summary.

### Fetch all feedback

Collect both review threads and issue comments as described in the normal
workflow, but paginate rather than accepting the first page:

- paginate `reviewThreads(first: 100, after: $endCursor)` and request
  `pageInfo { hasNextPage endCursor }`;
- retain thread ID, resolution and outdated state, path/line data, and every
  comment with its author, body, creation and update time, reply relationship,
  node ID, and database ID;
- if a thread contains more comments than one nested page, paginate that
  thread's comments separately;
- fetch issue comments with REST pagination and flatten all pages.

Filter only:

- non-review notes from the PR author;
- replies and summaries whose IDs are already recorded in the handoff;
- automated status notifications, duplicate summaries, and pure
  acknowledgments that contain no request or claim.

Keep substantive feedback from human and bot reviewers.

### Reconcile known items

- A manually resolved thread becomes `resolved-externally`.
- A deleted comment becomes `removed`.
- A materially edited comment or a new substantive reply becomes
  `needs-retriage`; invalidate its old approval.
- Keep outdated but unresolved threads unless evidence shows that the concern
  was superseded. An outdated code anchor does not prove the concern vanished.
- Before retrying a commit, push, reply, resolution, issue creation, or summary,
  inspect git or GET the remote object. Never infer failure from a timeout and
  blindly repeat a side effect.

If reconciliation finds any `needs-triage` or `needs-retriage` item and no
triage is currently `awaiting-approval`, this invocation is a delta-triage
unit. Do not process an already approved item in the same session. If a
triage is already `awaiting-approval`, do not open a second triage unit — fold
the newly reconciled items into that same pending table before presenting it
(see "Start of every invocation", priority 1).

## Unit 1 — Initial triage

Use this unit when no handoff exists.

1. Reject automatic migration when `.pr-review/plan-*.md` indicates an
   in-progress normal-mode run.
2. Identify and bind the current PR.
3. Discover the repository's required safeguards, but do not run the baseline
   in this triage-only session.
4. Fetch and inventory all current unresolved feedback with pagination.
5. Inspect only the repository evidence needed to assess each item.
6. Triage every current item in this session using the normal classifications.
7. For every item, record both:
   - its classification;
   - its exact proposed action, such as fix; ask one question; reply only; reply
     and resolve; create a follow-up issue; or take no remote action.
8. Group only a proposed atomic cascade, and make the grouping visible for user
   approval.
9. Write the provisional handoff with `Status: awaiting-approval` before
   presenting the triage.
10. Present the compact triage table and wait for explicit approval.
11. Apply user overrides, record approval in the handoff, set approved items to
    `pending`, set `Status: ready`, and stop.

Do not edit application code, run the baseline, post GitHub replies, create
issues, resolve threads, commit, or push during initial triage.

If the user does not approve, retain the provisional handoff so a fresh
handoff session can resume the approval gate.

## Unit 2 — Delta triage

Use this unit whenever reconciliation finds new or materially changed feedback.

1. Triage only the delta.
2. Preserve decisions and evidence for unchanged items.
3. For a reviewer answer to a clarification, update the original stable item
   rather than creating another queue entry.
4. Write the proposed delta with `awaiting-approval`.
5. Present only the new or changed decisions and exact actions.
6. After approval, update the queue and stop without implementation.

Order approved work by:

1. `NEEDS_CLARIFICATION`
2. `MUST_FIX`
3. `SHOULD_FIX`
4. `PARK`
5. `OUT_OF_SCOPE` and non-actionable acknowledgments

Within a class, preserve discovery order. A newly approved higher-priority item
may move ahead of lower-priority pending work but must not reorder earlier items
in its own class.

An explicit user override to a pending item also makes the current invocation a
decision unit: update its class/action and stop. Keep completed entries immutable;
a change to completed work becomes a new explicit follow-up item.

## Unit 3 — Process one approved item

Use this unit when reconciliation finds no delta and at least one item is
pending or already `in-progress`.

### Select and record

1. Resume the recorded `in-progress` item before selecting another.
2. Otherwise select the first pending item in queue order.
3. Write the current item, base commit, concise plan, acceptance criteria,
   expected paths, and `Status: in-progress` before editing or posting remotely.

Keep the plan inside `HANDOFF.md`; do not create a separate per-comment plan
file in handoff mode.

### Protect existing work

- Resume edits explicitly recorded for the current item.
- Preserve unrelated changes in non-overlapping files and stage only item-owned
  paths.
- If ownership is uncertain or another change overlaps an item-owned file, stop
  for user guidance.
- Never revert changes that predate the handoff session.

### Establish or reuse the baseline

Reuse the recorded pre-edit baseline only when:

- `HEAD` equals the last verified commit; and
- the worktree is clean.

Otherwise run the discovered baseline safeguards before editing. If unrelated
dirty changes make a failure ambiguous, stop rather than attributing it to the
selected item.

The first implementation session must run the baseline because triage only
discovered the commands.

### Complete the approved action

For a code fix or atomic cascade:

1. Implement the smallest complete approved change.
2. Run targeted checks plus every project-mandated gate relevant to the change.
3. If validation fails, attempt to correct the item. If it remains incomplete,
   preserve clearly attributable edits, record the concise failure and next
   action, and stop. Do not commit or perform remote closure.
4. If the discovered scope materially exceeds the approved plan, checkpoint the
   partial work and stop before irreversible remote actions. The next session
   resumes the same item.
5. Commit one focused change, push it, reply using a body file, verify the reply
   with a GET, resolve only when approved, and verify resolution. Follow the
   normal workflow's commit and remote-write rules.
6. Record each milestone immediately, including commit SHA and remote IDs.

For `NEEDS_CLARIFICATION`, `PARK`, `OUT_OF_SCOPE`, or a no-op acknowledgment:

1. Perform only the exact approved action.
2. Ask exactly one focused clarification question.
3. Do not create a follow-up issue for `PARK` unless that action was approved.
4. Do not resolve a rejected or parked thread unless resolution was approved.
5. Verify every posted comment or created issue and record its ID.

The item owns its complete lifecycle in this session: local change when needed,
verification, commit/push, reply, reply verification, resolution when approved,
and ledger update.

### Finish the unit

1. Compact the item into `Completed this cycle`.
2. Clear `Current item`.
3. Perform one lightweight final feedback fetch.
4. Record new or changed feedback as `needs-triage`, but do not triage it now.
5. Set the exact next action:
   - delta triage when feedback changed;
   - the next approved item when work remains;
   - finalization when the queue has no remaining actions.
6. Set `Status: ready` or `ready-to-finalize`.
7. Stop and tell the user to start a fresh session with
   `/pr-review-loop --handoff`.

Never process a second item in the same conversation.

## Unit 4 — Finalization

Use a dedicated fresh session when the handoff is `ready-to-finalize`.

1. Re-fetch and reconcile feedback. If a delta exists, perform delta triage
   instead and stop.
2. Check PR-body drift against the complete branch diff from the PR base.
3. Preserve the normal workflow's automatic body update when the existing body
   would materially mislead readers. Verify and record any edit.
4. Post one verified incremental summary covering only work since the previous
   recorded summary. Include awaiting clarification items whose approved
   question was posted.
5. Record the summary comment ID and URL.
6. Set `Status: complete`, retain the handoff, and stop.

If later feedback arrives on the same PR, increment `Cycle`, reopen the existing
item or add a new stable item, clear `Completed this cycle`, run delta triage,
and eventually post another incremental summary. Keep terminal queue entries
and prior summary IDs as audit evidence; do not edit or reconstruct prior
summaries.

## Final response for every unit

Keep the response compact:

- state which single unit completed or why it checkpointed;
- name the durable evidence, such as commit SHA or reply ID;
- give the exact next invocation when more work remains.

Do not offer to process another item in the same session.
