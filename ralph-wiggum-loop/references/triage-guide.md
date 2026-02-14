# Triage Guide

When classifying PR review comments, assign one of four categories:

## MUST_FIX
A blocking issue that must be resolved before the PR can merge.

Indicators:
- Reviewer explicitly says "blocking", "must fix", "required"
- Correctness bug or security issue
- Breaks tests or build
- Violates project conventions that are explicitly documented

## SHOULD_FIX
Non-blocking but worth addressing in this PR to improve quality.

Indicators:
- Reviewer says "nit", "suggestion", "consider", "ideally"
- Style or readability improvement
- Clear improvement with low risk and small effort
- Would reduce future confusion or maintenance burden

## PARK
Valid concern, but intentionally deferred outside this PR.

Use when:
- The fix requires changes in a different PR or component
- The effort is disproportionate to the PR scope
- It's a known existing issue not introduced by this PR
- You are deferring: create a follow-up issue and reference it in your reply

## OUT_OF_SCOPE
Not applicable to this PR; rejected with explanation.

Use when:
- Comment is based on a misunderstanding
- The suggested approach contradicts project conventions
- The comment refers to code not changed by this PR
- A prior discussion or decision already covers this

---

## Triage Tips

- When in doubt between MUST_FIX and SHOULD_FIX, ask: "Would a reviewer block merge over this?" If yes, MUST_FIX.
- When in doubt between SHOULD_FIX and PARK, ask: "Can this be done safely within this PR's scope?" If yes, SHOULD_FIX.
- If you need external knowledge (e.g., is this pattern idiomatic in this language/framework?), use Perplexity if available.
- Triage all comments before acting on any. This gives you a full picture before committing to changes.
