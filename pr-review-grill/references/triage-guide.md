# Triage Guide

When classifying PR review comments, assign one of five categories:

## MUST_FIX

A blocking issue that must be resolved before the PR can merge.

Indicators:

- Reviewer explicitly says "blocking", "must fix", or "required"
- Correctness bug or security issue
- Breaks tests or build
- Data loss or data-isolation risk
- Violates project conventions that are explicitly documented

## SHOULD_FIX

Non-blocking but worthwhile to address in this PR.

Indicators:

- Reviewer says "nit", "suggestion", "consider", or "ideally"
- Clear readability or maintenance improvement
- Small, safe improvement that reduces future confusion

## PARK

A valid concern intentionally deferred outside this PR.

Use when:

- The fix belongs in a different PR or component
- The effort is disproportionate to the PR scope
- It requires a team/API/architecture decision
- The user explicitly wants to discuss it with the team first

Record the deferral reason. Create a follow-up issue only when the user
explicitly approves that action.

## OUT_OF_SCOPE

Not applicable to this PR and rejected with an explanation.

Use when:

- The comment relies on a disproven premise
- The suggestion conflicts with a stronger project invariant
- The concern refers to code outside this PR's scope
- A prior decision already settles the issue

Distinguish a substantive rejected suggestion from a no-op acknowledgment.
They may need different replies and resolution actions.

## NEEDS_CLARIFICATION

The reviewer's intent is genuinely ambiguous and acting without confirmation
risks the wrong change.

Use when:

- Multiple valid interpretations lead to materially different code
- The suggestion is unclear or self-contradictory
- The reviewer must choose between incompatible API or behavior contracts

Do not use this category to avoid difficult work. Ask one focused question and
leave the thread unresolved.

## Discussion prompts

For every item, examine:

- What premise does the comment depend on?
- Can the premise be verified in code, schema, tests, or documentation?
- Does the repository already enforce a stronger invariant?
- Is the concern about correctness, safety, API contract, observability, style,
  or scope?
- Would a reasonable fix change behavior outside the PR's stated intent?
- Can the issue be fixed safely now, or does it require team agreement?

When the user supplies a corrected domain fact, replace the old premise in the
decision record and reassess the classification.
