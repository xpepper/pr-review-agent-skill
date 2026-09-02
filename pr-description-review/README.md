# PR Description Review

An [Agent Skills](https://agentskills.io) skill that reviews and improves pull
request descriptions so human and agent reviewers receive the context needed
for focused, evidence-based feedback.

## Install

```bash
npx skills add xpepper/pr-review-agent-skill/pr-description-review
```

## Usage

Review a GitHub pull request:

```text
/pr-description-review https://github.com/acme/payments/pull/42
```

Review the pull request associated with the current branch:

```text
Review the PR description for my current branch.
```

Review pasted text:

```text
Review this PR description for missing reviewer context and draft a better one:

<description>
```

The skill is read-only. It never publishes or edits the pull request.

## What it checks

- Purpose and user-visible outcome.
- End-to-end flow across relevant systems and actors.
- External contracts, invariants, identity mapping, and request preconditions.
- Deployment order, compatibility, and schema or generated-artifact provenance.
- Deliberate non-goals, accepted manual processes, and pre-existing limitations.
- What tests and mocks prove, and what remains unverified.
- Where reviewer attention is most valuable.

It evaluates only properties relevant to the change. Small local changes are
not forced into a distributed-systems template.

## Evidence calibration

The skill distinguishes:

- **Verified** facts supported by accessible code, tests, schemas, or
  deployment records.
- **Author-provided** team context that cannot be independently checked.
- **Unknown** facts that need confirmation.

This prevents the rewritten description from inventing frontend reachability,
upstream behavior, deployment status, production impact, or test coverage.

## Output

The result includes:

1. A `Ready`, `Needs context`, or `Misleading` verdict.
2. A table showing which reviewer-context properties are present or missing.
3. Likely reviewer misreads caused by hidden context, when applicable.
4. A complete improved PR-description draft.
5. A short list of author confirmations needed before publishing, when
   material facts remain unknown.

## Requirements

- Git and [`gh`](https://cli.github.com/) for GitHub PR or current-branch
  inputs.
- No tools are required when reviewing pasted description text.
