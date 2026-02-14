# PR Review Agent Skills

A collection of [Agent Skills](https://agentskills.io) for automating PR code review workflows.
Compatible with Claude Code, GitHub Copilot, Cursor, Windsurf, and 30+ other agents.

## Skills

### PR Review Loop

Addresses all open PR review comments one at a time using an opinionated, resumable workflow.
Works with any reviewer (human or bot).

**Install:**
```bash
npx skills add xpepper/pr-review-agent-skill/pr-review-loop -a claude-code
```

[See skill README →](pr-review-loop/README.md)

---

### Ralph Wiggum Loop *(coming soon)*

An automated Copilot review loop: triggers Copilot review, addresses feedback, and repeats
until all critical issues are resolved.

---

## Requirements

- `gh` CLI (recommended) or a GitHub token for REST API fallback
- Git

## License

MIT
