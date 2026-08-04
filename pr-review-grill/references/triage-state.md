# Triage State

The state file is `.pr-review/triage.json` at the repository root. Keep it
gitignored and local to the review session.

Example:

```json
{
  "version": 1,
  "phase": "discussion",
  "pr": {
    "owner": "org",
    "repo": "repository",
    "number": 42,
    "base": "master",
    "head": "feature/example"
  },
  "current_item": 1,
  "final_approval": false,
  "items": [
    {
      "key": "review-thread:PRRT_example",
      "type": "review-thread",
      "thread_id": "PRRT_example",
      "comment_ids": [123456],
      "author": "reviewer",
      "path": "src/example.rs",
      "line": 42,
      "body": "Review feedback",
      "group_key": null,
      "status": "decided",
      "classification": "PARK",
      "decision": "defer for team API discussion",
      "rationale": "The concern is valid, but changing the public scalar requires a team decision.",
      "implementation_notes": "Do not change code in this PR.",
      "remote_action": "leave-open"
    }
  ]
}
```

## Allowed values

`phase`:

- `preflight`
- `collection`
- `discussion`
- `approval`
- `processing`
- `summary`
- `complete`

Item `status`:

- `pending`
- `discussing`
- `decided`
- `processing`
- `processed`
- `parked`
- `awaiting-clarification`

`remote_action` should describe intent, not claim success. Examples:

- `reply-and-resolve`
- `reply-and-leave-open`
- `leave-open`
- `none`

After a remote action, add verification fields such as:

```json
{
  "reply_id": 987654,
  "reply_verified": true,
  "thread_resolved": true,
  "commit": "abc1234"
}
```

Never store tokens, credentials, or secrets in this file.
