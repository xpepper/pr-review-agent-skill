# pr-review-loop: triage approval gate + PR body drift check

**Date:** 2026-06-28
**Skill:** `pr-review-loop`
**Version bump:** 1.4.0 → 1.5.0 (additive workflow change)

## Problem

The happy-path definition for the `pr-review-loop` skill includes these checkable
expectations:

- Agent stops after triage, before addressing anything (presents the triage, waits for go-ahead)
- Comments are challenged, not blindly accepted — yet feedback is held in high regard (shared goal: highest-quality merge)
- Every comment evaluated against the actual codebase conventions / agent guidelines
- Each addressed comment ends up resolved
- Each addressed comment gets its own commit (no stacking)
- If new commits change the PR's scope vs. its body, the agent updates the PR body to avoid drift

The current `SKILL.md` already covers four of these (challenge/adapt/reject in
triage + processing, conventions via pre-flight + triage guide, resolve per
comment, one-commit-per-comment). Two are missing:

1. **No triage approval gate.** Step 4 (Triage) flows straight into Step 5
   (Process ONE comment at a time). There is no explicit "stop, present the
   triage to the user, wait for confirmation" boundary. The agent starts
   changing code, posting replies, and resolving threads before the user has
   seen or sanctioned the plan.

2. **No PR body drift handling.** Nothing in the skill compares the PR body
   against the scope of the new commits or updates it. Step 7 only posts a
   summary comment, leaving the PR description potentially stale.

## Goals

- Add an explicit, conversational triage approval gate between triage and
  processing.
- Add a PR body drift check after processing and before the summary.
- Keep the skill internally consistent (cross-references, numbering, `Do Not`
  list, Resumability, version).

## Non-goals

- No change to the triage classification framework itself (MUST_FIX /
  SHOULD_FIX / PARK / OUT_OF_SCOPE / NEEDS_CLARIFICATION).
- No change to the per-comment processing mechanics (plan files, safeguards,
  reply/resolve/verify flow).
- No persistence of the gate's approval state across fresh-context resumes
  (re-prompting on resume is safe and acceptable).

## Design

### Improvement 1 — Triage approval gate (new Step 5)

Insert a new step immediately after triage. The agent **stops** after
classifying every comment, presents the full triage to the user, and waits for
a go-ahead. Until the user responds, the agent does not touch code, post
replies, create plan files, or resolve anything.

**What is presented** — a compact table, one row per unresolved comment:

| Column | Content |
|--------|---------|
| Ref | author + `file:line` (review thread) or short excerpt (issue comment) |
| Class | MUST_FIX / SHOULD_FIX / PARK / OUT_OF_SCOPE / NEEDS_CLARIFICATION |
| Rationale | one line, grounded in codebase conventions / agent guidelines |

The rationale column is where the "challenge, don't blindly accept" expectation
becomes visible: each comment is shown as accepted, adapted, or pushed back on,
with a reason tied to the project's conventions — not blind agreement.

**What the user can do:**

- Approve as-is ("go ahead", "looks good").
- Adjust individual classifications ("treat #3 as PARK", "#5 is OUT_OF_SCOPE,
  convention is X"). The agent applies the overrides. If the changes are
  substantial, it re-presents the updated triage; otherwise it proceeds.

Only after explicit approval does the agent move on to processing.

**Resumability:** the gate is conversational state, not persisted to
`.pr-review/`. On a fresh-context resume, unresolved threads re-surface, the
agent re-triages and re-presents the gate. Re-prompting is safe because no work
is lost (each fix is committed and pushed before moving on). This is covered by
a one-line note in the Resumability section.

### Improvement 2 — PR body drift check (new step before Summary)

After all MUST_FIX / SHOULD_FIX comments are processed and before the summary
step, add a step that compares the PR body against the scope of the commits
made during this run.

**Detection heuristic:**

- Gather the commits made during this run (`git log` of the new commits) and
  the current PR body (`gh pr view`).
- **Drift** = the body would now mislead a reader about what the PR contains:
  added or removed behaviour, a changed approach, or scope the body does not
  mention.
- **Not drift** = pure bug-fix tweaks that do not change the PR's stated intent.
  Do not churn the body needlessly.

**Behaviour (update-then-report):**

- If drift is detected, update the PR body via `gh pr edit --body-file`,
  preserving the parts of the body that are still accurate.
- Record the update in the Step 7/8 summary (e.g. an "Updated PR body to
  reflect …" line).
- This is outward-facing but is already sanctioned by the upfront triage
  approval and is surfaced in the summary, so no second interactive gate is
  added.

### Structural changes to SKILL.md

Full renumbering is used (chosen over inserting `4.5`/`6.5`-style sub-steps)
because internal cross-references must be updated consistently regardless.

Resulting step order:

1. Pre-flight *(unchanged)*
2. Get Current PR Number and Basic Info *(unchanged)*
3. Collect All Unresolved PR Feedback *(unchanged)*
4. Triage *(unchanged content; remove the implicit "flow straight into
   processing" expectation)*
5. **Triage approval gate** *(new)*
6. Process ONE comment at a time *(was Step 5; all internal "Step 5x" and
   "Step 4b" references renumbered to "Step 6x" / "Step 5b" as appropriate)*
7. Stop condition *(was Step 6)*
8. **PR body drift check** *(new — placed after stop condition, before summary)*
9. Summary *(was Step 7; add the body-update line to the template)*

Additional edits:

- **`Do Not` list:** add an item — "Start processing comments before the user
  has approved the triage."
- **Resumability section:** add the one-line note about the gate re-prompting on
  resume.
- **Frontmatter:** bump `version` to `1.5.0`.
- **Cross-references:** audit and update every internal "Step N" reference
  (notably the `Process` step's `5a–5h` sub-steps and the Resumability section's
  "continue from Step 4b").

## Verification

- Re-read the edited `SKILL.md` end to end; confirm no stale "Step N" reference
  remains and the gate/drift steps are internally consistent.
- Run `./package-skill.sh` and confirm the `pr-review-loop` skill packages
  without error.

## Risks / follow-ups

- The drift heuristic is judgment-based; over-eager body rewrites are the main
  risk, mitigated by the explicit "not drift" guidance.
- Renumbering touches many cross-references; the end-to-end re-read is the guard
  against a missed reference.
